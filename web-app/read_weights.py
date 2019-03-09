

def get_weights_json():
    a = []
    with open('static/weights.csv', 'r') as f:
        for line in f:
            a.append('[{}]'.format(line.strip()))
    print 'weights = [{}]'.format(', '.join(a)) 