"""module for reading client/server configs"""

def client_config(file):
  """returns tuple containing client config"""
  configs = []
  for line in open(file, "r"):
    configs.append(line[:-1])

  server_ip = configs[0]
  server_port = int(configs[1])
  client_port = int(configs[2])
  transferred_file = configs[3]
  rcv_window_size = int(configs[4])

  return server_ip, server_port, client_port, transferred_file, rcv_window_size


def server_config(file):
  """returns tuple containing server config"""
  configs = []
  for line in open(file, "r"):
    configs.append(line[:-1])

  server_port = int(configs[0])
  snd_window_size = configs[1]
  rnd_seed = int(configs[2])
  loss_prop = float(configs[3])

  return server_port, snd_window_size, rnd_seed, loss_prop
