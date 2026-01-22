from collections import OrderedDict


# Default EOF symbol
def EOF():
    return 256


# Default ESC symbol for PPM model
def ESC():
    return 257


class FrequencyTable:
    def __init__(self, symbols=None):
        self.alphabet = []
        self.frequencies = OrderedDict()
        self.cumulative_ranges = {}
        self.nsymbols = 0

        # Build a table with the symbols and get the probabilities
        if symbols:
            for s in symbols:
                self.add(s)
            self.calculateProbabilities()

    # Method use for create the default Frequency Table, don't update the probabilities when a new symbol is added
    def add(self, symbol):
        if symbol in self.frequencies:
            self.frequencies[symbol] += 1
        else:
            self.alphabet.append(symbol)
            self.frequencies[symbol] = 1
        self.nsymbols += 1

    # Method used for update the frequency of the symbols and calculate the new probabilities in case of encode/decode
    def updateFreqs(self, symbol):
        self.frequencies[symbol] += 1
        self.nsymbols += 1
        self.calculateProbabilities()

    # Update the cumulative ranges of the symbols
    def calculateProbabilities(self):
        ranges = {}
        accumulate = 0

        for symbol in self.alphabet:
            low = accumulate
            high = accumulate + self.frequencies[symbol]
            ranges[symbol] = (low, high)
            accumulate = high

        self.cumulative_ranges = ranges


# Build a default table with 256 bits + EOF symbol
def build_default_FrequencyTable(eof_symbol=EOF()):
    freqs = FrequencyTable()

    for symbol in range(256):
        freqs.add(symbol)

    freqs.add(eof_symbol)

    freqs.calculateProbabilities()
    return freqs
