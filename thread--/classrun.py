

import time
import threading


class myth(threading.Thread):

    def __init__(self, argv1, argv2):
        super().__init__()
        self.argv1 = argv1
        self.argv2 = argv2


    def run(self):
        for i in range(15):
            print(self.argv1, self.argv2)
            time.sleep(1)



th = myth("参数1", "参数2")

th.start()

th.join()

print("done")
