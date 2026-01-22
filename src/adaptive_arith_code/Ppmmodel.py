try:
    from FrequencyTable import FrequencyTable, EOF, ESC
except ImportError:
    from .FrequencyTable import FrequencyTable, EOF, ESC


# Implementation of the Prediction Partial Matching
# Default escape symbol 257, due to 256 maybe is use for EOF symbol.
class PPMModel:
    def __init__(self, model_order, escape_symbol=ESC(), eof_symbol=EOF()):
        self.model_order = model_order
        self.contexts = {}

        # set a default esc symbol used
        self.escape_symbol = escape_symbol
        # set a default eof symbol used to implement in the tables
        self.eof_symbol = eof_symbol

        # Orden -1: Garantiza que todos los bytes (0-255) sean codificables
        self.order_minus_1 = FrequencyTable(range(256))

        # Initializate Orden 0 (empty context) With esc and eof symbol
        self.root_ctx = tuple()
        self.contexts[self.root_ctx] = FrequencyTable()
        self.contexts[self.root_ctx].add(self.escape_symbol)
        self.contexts[self.root_ctx].add(self.eof_symbol)
        self.contexts[self.root_ctx].calculateProbabilities()

    def get_context_table(self, context):
        # if the table don't exist, we create a new FrequencyTable
        if context not in self.contexts:
            table = FrequencyTable()
            table.add(self.escape_symbol)
            table.calculateProbabilities()
            self.contexts[context] = table
        return self.contexts[context]

    # update the actual context and all the sufix (below orders)
    def update(self, history, symbol):
        for i in range(len(history) + 1):
            ctx = history[i:]
            # if the context is not in the dictionary, create the FrequencyTable
            if ctx not in self.contexts:
                self.contexts[ctx] = FrequencyTable()
                self.contexts[ctx].add(self.escape_symbol)
                if ctx == tuple():
                    self.contexts[ctx].add(self.eof_symbol)

            self.contexts[ctx].add(symbol)
            self.contexts[ctx].calculateProbabilities()