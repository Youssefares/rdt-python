from random import sample, seed

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

if __name__ == '__main__':
    p = 0.3
    drop_current = get_loss_simulator(p, 1000)
    l = sum([drop_current() for _ in range(1000)]) / 1000
    assert l == p
