from random import sample, seed, randint

def get_loss_simulator(probability, seed_num):
    """
    Simulate package loss by returning a function that randomly return
    whether to drop the current package or not keeping the probability
    as defined
    """
    seed(seed_num)
    current_i = 0
    drop_indicies = sample(range(0, 10), int(probability * 10))
    def to_drop_current():
        nonlocal current_i, drop_indicies
        drop = False
        if current_i in drop_indicies:
            drop = True
        current_i += 1
        if current_i % 10 == 0:
            drop_indicies = sample(range(0, 10), int(probability * 10))
            current_i = 0
        return drop

    return to_drop_current

def get_corrupt_simulator(probability, seed_num):
    """
    Simulates Packet corruption using the same loss simulator but not dropping
    the packet entirely but instead change a random bit to corrupt it
    """
    seed(seed_num)
    corrupt_it = get_loss_simulator(probability, seed_num)

    def corrupt_or_not(packet):
        if corrupt_it():
            r = randint(0, len(packet) - 1)
            packet = packet[0: r] + bytes(1) + packet[r:]
        return packet
    
    return corrupt_or_not

if __name__ == '__main__':
    p = 0.3
    drop_current = get_loss_simulator(p, 1000)
    l = sum([drop_current() for _ in range(1000)]) / 1000
    assert l == p
