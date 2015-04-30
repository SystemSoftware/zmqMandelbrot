import zmq
import argparse

# CLI Arugmente parsen und uebernehmen
parser = argparse.ArgumentParser(description='Worker')
parser.add_argument('--port', required=True, type=int,
help="Port for the worker, i.e. 5555 - Warning - reserves this port and port +1!")
args = parser.parse_args()

print("Worker: " + str(args.port))

# ZMQ Context erstellen
context = zmq.Context()
# Hoere auf Pull Verbindung vom Server
# auf Port, Verbindung um Ergebnisse zu pushen 
push_result = context.socket(zmq.PUSH)
push_result.bind("tcp://*:" + str(args.port))
# Hoere auf Push Verbindung vom Server
# auf Port + 1, Verbindung um Arbeit zu pullen 
pull_work = context.socket(zmq.PULL)
pull_work.bind("tcp://*:" + str(int(args.port)+1))
print("Wait for connection from coordinator")

while True:
    result = []
    result_element = {}
    # Warte auf nacheste Arbeitsanweisung vom Server
    s = pull_work.recv_json()
    # Habe Arbeit erhalten
    print("? "),     

    # Berechene Bildausschnitt
    ky = s["sizeY_min"] 
    while ky < s["sizeY_max"]:
      for kx in range(s["sizeX"]):
          #c = complex(s["xa"] + (s["xb"] - s["xa"]) * kx / s["sizeX"], s["ya"] + (s["yb"] - s["ya"]) * s["ky"] / s["sizeY"])
          c = complex(s["xa"] + (s["xb"] - s["xa"]) * kx / s["sizeX"], s["ya"] + (s["yb"] - s["ya"]) * ky / s["sizeY"])
          z = complex(0.0, 0.0)
          for i in range(s["iterations"]):
              z = z * z + c
              if abs(z) >= 2.0:
                  break
          # Speichere die Resultate nach jedem Durchlauf in einem Dictionary / Hash Table
          result_element["kx"] = kx
          result_element["ky"] = ky
          result_element["red"] = (i % 4 * 64)
          result_element["green"] = (i % 8 * 32)
          result_element["blue"] = (i % 16 * 16)
          # ... und fuege die einzelnen Dictionarys in eine Liste ein
          result.append(result_element.copy())
      ky += 1
      print("#"),

    # Berechnung beendet, pushe die Resultate zum Server
    push_result.send_json(result)
    print("! ")


        


