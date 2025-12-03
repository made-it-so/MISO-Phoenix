from miso_client.client import Miso
m = Miso("test-key")
print("SDK Test:", m.think("Ping"))
