import zmq
import argparse
from PIL import Image
from timeit import default_timer as timer
import threading

# CLI Arugmente parsen und uebernehmen 
parser = argparse.ArgumentParser(description='Cordinator')
parser.add_argument('--size', type=int, nargs=2, default = [640, 480],
help="Size of Calculation, i.e. 640 480")
parser.add_argument('--iterations', type=int, default = 18,
help="Count of iterations, i.e. 18")
parser.add_argument('--cut_x', nargs=2, default = [-2.0, 1.0],
help="Visible Part on X Axis, i.e. -2.0 1.0")
parser.add_argument('--cut_y', nargs=2, default = [-1.5, 1.5],
help="Visible Part on Y Axis, i.e. -1.5 1.5")
parser.add_argument('--threads', required=True, type=int, default = 1,
help="Count of threads, i.e. 1")
args = parser.parse_args()

# Speichere Settings in Dictonary / Hashtable
# fuer spaeteren Austausch mit Threads
s ={
    "sizeX": args.size[0],
    "sizeY": args.size[1],
    "sizeY_min": args.size[1],
    "sizeY_max": args.size[1],
    "iterations": args.iterations,
    "xa" : args.cut_x[0],
    "xb" : args.cut_x[1],
    "ya" : args.cut_y[0],
    "yb" : args.cut_y[1],
    "ky" : 0
}

result_list = []
# Anzahl der Threads bestimmen
thread_count = args.threads

# ZMQ Context erstellen
# ein PULL und ein PUSH Kanal
context = zmq.Context.instance()
pull_result = context.socket(zmq.PULL)
push_work = context.socket(zmq.PUSH)

# definiere einen Worker Thread
def worker(num, context=None):
    # Ausgabe der Worker ID
    print 'Worker: %s \n' % num
    # ZMQ Context erstellen
    # und INPROC Verbindung aufbauen
    context = context or zmq.Context.instance()
    push_result = context.socket(zmq.PUSH)
    push_result.bind("inproc://" + str(num))
    pull_work = context.socket(zmq.PULL)
    pull_work.bind("inproc://" + str(num+100))
    
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

    # Berechnung beendet, pushe die Resultate zum Mainthread
    push_result.send_json(result)
    print("! ")
    # gehe zueruck zum Mainthread
    return

# Erstelle die einzelnen Threads und baue die INPROC Verbindung auf
threads = []
for i in range(thread_count):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()
    pull_result.connect("inproc://" + str(i))
    push_work.connect("inproc://" + str(i+100))
 
# Neues Bild im Speicher erstellen
im = Image.new("RGB",(s["sizeX"],s["sizeY"]))
# Timer starten
time_start = timer()

# Zerlege Bild an der Y Achse in (Y-Achse / Anzahl Nodes)
# grosse Teile und pushe die Anzahl von Teilen per push_work
# an die Nodes zur Berechnung
sizeY = 0
computeSize = (s["sizeY"] / thread_count)
while sizeY < s["sizeY"]:
  s["sizeY_min"] = sizeY
  s["sizeY_max"] = (sizeY + computeSize)
  sizeY += computeSize
  push_work.send_json(s)

# Empfange die fertigen Berechnungen und fuege die Listen zusammen
while thread_count > 0:  
  result = pull_result.recv_json()
  result_list += result
  thread_count -= 1   

# Stoppe den Timer fuer die Berechnung
time_delta = timer() - time_start  

# Gehe durch die einzelnen Punkte und zeichne diese ins Bild    
for result_elements in result_list:
    im.putpixel((result_elements["kx"],result_elements["ky"]),(result_elements["red"],result_elements["green"],result_elements["blue"]))   

# Speichere das fertige Bild
im.save("mandelbrot.png", "PNG")

# Gebe Ergebniss fuer Berechnung aus
print "Mandelbrot created in %f s" % time_delta

