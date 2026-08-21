from dggs import DDGS

def test():
    results = DDGS().news('vietnam', max_results=3)
    print(list(results))

test()
