from multiprocessing import Value, Lock
shared_x = Value('i', 256)  # 'd'表示双精度浮点
shared_y = Value('i', 256)
coord_lock = Lock()