#include <Adafruit_MAX31865.h>
#include <PID_v1.h>
#include <zephyr/kernel.h>

// ==========================================
// 1. IMPOSTAZIONI SENSORI E PIN
// ==========================================
Adafruit_MAX31865 max_fredda = Adafruit_MAX31865(10, 11, 12, 13);
Adafruit_MAX31865 max_calda  = Adafruit_MAX31865(8,  11,  7, 13);

#define RREF      430.0
#define RNOMINAL  100.0
#define PIN_MOSFET  9

bool MODO_RAFFREDDAMENTO = true;

// ==========================================
// 2. GENERATORE PWM TRAMITE KERNEL ZEPHYR (100 Hz)
// ==========================================
struct k_timer pwm_timer;
const uint32_t period_us = 10000;  // 10.000 us = 100 Hz
volatile uint32_t duty_us = 0;
bool pwm_is_on = false;

void pwm_timer_isr(struct k_timer *timer_id) {
  uint32_t current_duty = duty_us;
  if (current_duty == 0) {
    digitalWrite(PIN_MOSFET, LOW);
    pwm_is_on = false;
    k_timer_start(&pwm_timer, K_USEC(period_us), K_NO_WAIT);
  } else if (current_duty >= period_us) {
    digitalWrite(PIN_MOSFET, HIGH);
    pwm_is_on = true;
    k_timer_start(&pwm_timer, K_USEC(period_us), K_NO_WAIT);
  } else {
    if (pwm_is_on) {
      digitalWrite(PIN_MOSFET, LOW);
      pwm_is_on = false;
      k_timer_start(&pwm_timer, K_USEC(period_us - current_duty), K_NO_WAIT);
    } else {
      digitalWrite(PIN_MOSFET, HIGH);
      pwm_is_on = true;
      k_timer_start(&pwm_timer, K_USEC(current_duty), K_NO_WAIT);
    }
  }
}

// ==========================================
// 3. SEQUENZA DI TEST — tempi in millisecondi
//
//  [  0 s -  300 s]  INIT + STANDBY iniziale   (5 min)
//  [300 s - 2100 s]  SP1 = 22 gradi C          (30 min)
//  [2100 s - 3000 s] RIPOSO 1                  (15 min)
//  [3000 s - 4800 s] SP2 = 20 gradi C          (30 min)
//  [4800 s - 5700 s] RIPOSO 2                  (15 min)
//  [5700 s - 6900 s] SP3 = 18 gradi C          (20 min)
//  [6900 s +       ] fine test -> STANDBY
//
//  Totale: 6900 s = 115 minuti
// ==========================================
const unsigned long T_SP1_START = 300000UL;
const unsigned long T_SP1_END   = 2100000UL;
const unsigned long T_SP2_START = 3000000UL;
const unsigned long T_SP2_END   = 4800000UL;
const unsigned long T_SP3_START = 5700000UL;
const unsigned long T_SP3_END   = 6900000UL;

const double SP1 = 22.0;
const double SP2 = 20.0;
const double SP3 = 18.0;

// Restituisce true se la sequenza richiede il controllo, e imposta sp_out
bool getSequenzaTest(unsigned long t_ms, double &sp_out) {
  if (t_ms >= T_SP1_START && t_ms < T_SP1_END) { sp_out = SP1; return true; }
  if (t_ms >= T_SP2_START && t_ms < T_SP2_END) { sp_out = SP2; return true; }
  if (t_ms >= T_SP3_START && t_ms < T_SP3_END) { sp_out = SP3; return true; }
  sp_out = 0.0;
  return false;
}

// ==========================================
// 4. VARIABILI DI SISTEMA
// ==========================================
enum State { INIT, STANDBY, ACTIVE_CONTROL, THERMAL_FAULT };
State currentState = INIT;

float T_calda;
float T_fredda;

unsigned long tempo_ultimo_ciclo = 0;
const unsigned long INTERVALLO_CICLO = 1000;  // 1 Hz
#define TIME_WAIT_BOOT 60000 // [ms]

// ==========================================
// 5. VARIABILI PID
// ==========================================
double Setpoint_PID = SP1;
double Input_PID    = 25.0;
double Output_PID   = 0.0;

// Guadagni allineati al gemello digitale Simulink
double Kp = 0.5, Ki = 0.01, Kd = 0.0;

PID mioPID(&Input_PID, &Output_PID, &Setpoint_PID, Kp, Ki, Kd, REVERSE);

// ==========================================
// 6. SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_MOSFET, OUTPUT);
  digitalWrite(PIN_MOSFET, LOW);

  k_timer_init(&pwm_timer, pwm_timer_isr, NULL);
  k_timer_start(&pwm_timer, K_USEC(1), K_NO_WAIT);

  max_fredda.begin(MAX31865_4WIRE);
  max_calda.begin(MAX31865_4WIRE);

  if (MODO_RAFFREDDAMENTO) {
    mioPID.SetControllerDirection(REVERSE);
  } else {
    mioPID.SetControllerDirection(DIRECT);
  }

  mioPID.SetOutputLimits(0, 100);
  mioPID.SetSampleTime(1000);
  mioPID.SetMode(AUTOMATIC);

  delay(TIME_WAIT_BOOT);

  // Intestazione CSV per telemetria
  Serial.println("t_ms,setpoint,T_fredda,T_calda,output_pid,stato");
}

// ==========================================
// 7. LOOP PRINCIPALE (1 Hz)
// ==========================================
void loop() {

  unsigned long tempo_attuale = millis();

  if (tempo_attuale - tempo_ultimo_ciclo >= INTERVALLO_CICLO) {
    tempo_ultimo_ciclo = tempo_attuale;

    // --- Lettura sensori ---
    T_fredda = max_fredda.temperature(RNOMINAL, RREF);
    T_calda  = max_calda.temperature(RNOMINAL, RREF);

    bool sonda_guasta = false;

    uint8_t fault_fredda = max_fredda.readFault();
    if (fault_fredda) {
      max_fredda.clearFault();
      sonda_guasta = true;
    }
    uint8_t fault_calda = max_calda.readFault();
    if (fault_calda) {
      max_calda.clearFault();
      sonda_guasta = true;
    }

    if (sonda_guasta) {
      duty_us = 0;
      currentState = THERMAL_FAULT;
    }

    // --- Sequenza temporizzata ---
    double sp_corrente;
    bool attivo = getSequenzaTest(tempo_attuale, sp_corrente);

    // --- Macchina a stati ---
    switch (currentState) {

      case INIT: {
        if (T_calda > -50.0 && T_fredda > -50.0) {
          currentState = STANDBY;
        } else {
          currentState = THERMAL_FAULT;
        }
        break;
      }

      case STANDBY: {
        duty_us = 0;
        if (attivo && T_calda <= 60.0) {
          Setpoint_PID = sp_corrente;
          // Reset integrale PID prima di ogni nuova fase attiva
          mioPID.SetMode(MANUAL);
          Output_PID = 0.0;
          mioPID.SetMode(AUTOMATIC);
          currentState = ACTIVE_CONTROL;
        }
        break;
      }

      case ACTIVE_CONTROL: {
        if (T_calda > 60.0) {
          duty_us = 0;
          currentState = THERMAL_FAULT;
          break;
        }
        if (!attivo) {
          duty_us = 0;
          currentState = STANDBY;
          break;
        }

        // Aggiorna setpoint se la sequenza e' passata alla fase successiva
        if (Setpoint_PID != sp_corrente) {
          Setpoint_PID = sp_corrente;
        }

        Input_PID = MODO_RAFFREDDAMENTO ? T_fredda : T_calda;
        mioPID.Compute();
        duty_us = (uint32_t)((Output_PID / 100.0) * period_us);
        break;
      }

      case THERMAL_FAULT: {
        duty_us = 0;
        break;
      }
    }

    // --- Telemetria CSV (1 riga/secondo) ---
    const char* stato_str;
    switch (currentState) {
      case INIT:           stato_str = "INIT";           break;
      case STANDBY:        stato_str = "STANDBY";        break;
      case ACTIVE_CONTROL: stato_str = "ACTIVE_CONTROL"; break;
      case THERMAL_FAULT:  stato_str = "THERMAL_FAULT";  break;
      default:             stato_str = "UNKNOWN";        break;
    }

    Serial.print(tempo_attuale - TIME_WAIT_BOOT);       Serial.print(",");
    Serial.print(sp_corrente, 1);                       Serial.print(",");
    Serial.print(T_fredda, 2);                          Serial.print(",");
    Serial.print(T_calda,  2);                          Serial.print(",");
    Serial.print(Output_PID, 1);                        Serial.print(",");
    Serial.println(stato_str);
  }
}
