


# from multiprocessing.managers import SharedMemoryManager

from typing import (
    Dict,
)

from multiprocessing.shared_memory import SharedMemory



class SMM:

    def __init__(self):

        self.sm: Dict[str, SharedMemory] = {}


    def put(self, data):
        
