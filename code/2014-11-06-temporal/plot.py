import numpy as np
import matplotlib.pyplot as plt

y = np.linspace(0, 6)
t = np.linspace(0, 2*np.pi, 20)
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_ylim(0, 6)
ax.set_xlim(-1, 1)
ax.set_xlabel("u")
ax.set_ylabel("y")
ax.grid()
xdata, ydata = [], []
#ax.figure.canvas.draw()
for i in range(len(t)):
    u = np.exp(-y/np.sqrt(2))*np.sin(t[i]-y/np.sqrt(2))
    line.set_data(u, y)
    if i < 10:
        plt.savefig("step0%d.png" % i)
    else:
        plt.savefig("step%d.png" % i)
