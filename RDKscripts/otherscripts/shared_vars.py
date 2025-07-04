from multiprocessing import Value, Lock

# 共享的int变量及锁
shared_x = Value('i', 0)
shared_y = Value('i', 0)
data_lock = Lock()
#320是x坐标的中心点