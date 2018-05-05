from GoBackN.GoBackNClient import GoBackNClient

if __name__ == '__main__':
    GoBackNClient(('localhost', 5757)).request_file(('localhost', 6222), 'public/big_file.txt')
    # GoBackNClient(('localhost', 5858)).request_file(('localhost', 6222), 'public/big_file.txt')