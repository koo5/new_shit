
import grpc
import helloworld_pb2
import helloworld_pb2_grpc
from threading import Thread

def run():
  channel = grpc.insecure_channel('localhost:50051')
  stub = lemon_pb2_grpc.MenuGuiStub(channel)
  response = stub.noticeThatServerDataChanged()
  print("ok")

def notifyThatServerDataChanged():
  Thread(run).start()

if __name__ == '__main__':
  notifyThatServerDataChanged()
