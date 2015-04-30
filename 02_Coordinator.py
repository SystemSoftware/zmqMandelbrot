import zmq
import argparse
from PIL import Image
from timeit import default_timer as timer

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
parser.add_argument('--nodes', required=True, nargs='*',
help="Enter List of IP Adresses and Ports of Nodes, i.e. 127.0.0.1 5555 192.168.1.2 5555")
args = parser.parse_args()

# Speichere Settings in Dictonary / Hashtable
# fuer spaeteren Austausch mit Workern
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
# Anzahl der nodes bestimmen
nodes = (len(args.nodes)/2)

# ZMQ Context erstellen
# ein PULL und ein PUSH Kanal
context = zmq.Context()
# pull_result um fertige Arbeit zu pullen
pull_result = context.socket(zmq.PULL)
# push_work um neue Arbeitspakete zu pushen
push_work = context.socket(zmq.PUSH)

addr = 0
while addr < len(args.nodes):
  NodeIP = args.nodes[addr]
  NodePort = args.nodes[addr+1]
  pull_result.connect("tcp://" + NodeIP + ":" + NodePort)
  push_work.connect("tcp://" + NodeIP + ":" + str(int(NodePort)+1))
  addr += 2

# Neues Bild im Speicher erstellen
im = Image.new("RGB",(s["sizeX"],s["sizeY"]))
# Timer starten
time_start = timer()

# Zerlege Bild an der Y Achse in (Y-Achse / Anzahl Nodes)
# grosse Teile und pushe die Anzahl von Teilen per push_work
# an die Nodes zur Berechnung
sizeY = 0
computeSize = (s["sizeY"] / nodes)
while sizeY < s["sizeY"]:
  s["sizeY_min"] = sizeY
  s["sizeY_max"] = (sizeY + computeSize)
  sizeY += computeSize
  push_work.send_json(s)

# Empfange die fertigen Berechnungen und fuege die Listen zusammen
while nodes > 0:  
  result = pull_result.recv_json()
  result_list += result
  nodes -= 1   

# Stoppe den Timer fuer die Berechnung
time_delta = timer() - time_start

# Gehe durch die einzelnen Punkte und zeichne diese ins Bild
for result_elements in result_list:
  im.putpixel((result_elements["kx"],result_elements["ky"]),(result_elements["red"],result_elements["green"],result_elements["blue"]))   

# Speichere das fertige Bild
im.save("mandelbrot.png", "PNG")

# Gebe Ergebniss fuer Berechnung aus
print "Mandelbrot created in %f s" % time_delta
