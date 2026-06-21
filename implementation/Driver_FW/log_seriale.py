"""
log_seriale.py — Logger seriale per test Peltier Digital Twin
Salva la telemetria CSV dell'Arduino nella stessa cartella di questo script.

Uso:
    python log_seriale.py

Requisiti:
    pip install pyserial
"""

import serial
import serial.tools.list_ports
import csv
import datetime
import os
import sys
import time

BAUD_RATE = 115200
CARTELLA  = os.path.dirname(os.path.abspath(__file__))


def trova_porta():
    porte = list(serial.tools.list_ports.comports())
    if not porte:
        print("ERRORE: nessuna porta COM trovata.")
        print("       Verifica che l'Arduino sia collegato e i driver siano installati.")
        sys.exit(1)

    if len(porte) == 1:
        p = porte[0]
        print(f"Porta rilevata automaticamente: {p.device}  ({p.description})")
        return p.device

    print("Porte COM disponibili:")
    for i, p in enumerate(porte):
        print(f"  [{i}]  {p.device}  —  {p.description}")

    while True:
        try:
            scelta = int(input("Scegli il numero della porta: "))
            return porte[scelta].device
        except (ValueError, IndexError):
            print("Scelta non valida, riprova.")


def main():
    porta = trova_porta()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = os.path.join(CARTELLA, f"test_peltier_{timestamp}.csv")

    print(f"\nConnessione a {porta} @ {BAUD_RATE} baud...")
    print(f"Log salvato in: {nome_file}")
    print("Premi Ctrl+C per terminare il log.\n")
    print("NOTA: assicurati che il Serial Monitor di Arduino IDE sia CHIUSO.")
    print("-" * 60)

    righe = 0
    ser = None

    try:
        ser = serial.Serial(porta, BAUD_RATE, timeout=2)
        # L'apertura della porta resetta l'Arduino: il test parte da t=0.
        time.sleep(2)

        with open(nome_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            while True:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                # Mostra a schermo
                print(line)

                # Salva nel CSV (la prima riga è già l'intestazione inviata dal FW)
                writer.writerow(line.split(","))
                f.flush()   # flush immediato: nessun dato perso in caso di Ctrl+C
                righe += 1

    except KeyboardInterrupt:
        print(f"\n{'=' * 60}")
        print(f"Log terminato. {righe} righe scritte.")
        print(f"File: {nome_file}")

    except serial.SerialException as e:
        print(f"\nERRORE porta seriale: {e}")
        print("Chiudi il Serial Monitor di Arduino IDE e riprova.")

    finally:
        if ser and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
