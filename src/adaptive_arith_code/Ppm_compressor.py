try:
    from Ppmmodel import PPMModel
    from adaptiveArithmeticCode import ArithmeticCodding
    from FrequencyTable import EOF, ESC
except ImportError:
    from .Ppmmodel import PPMModel
    from .adaptiveArithmeticCode import ArithmeticCodding
    from .FrequencyTable import EOF, ESC

class PPMCompressor:
    def __init__(self, model_order=1, eof_symbol=EOF(), escape_symbol=ESC()):
        self.model_order = model_order
        self.model = PPMModel(model_order, escape_symbol=escape_symbol, eof_symbol=eof_symbol)
        self.coder = ArithmeticCodding(precision=32, eof_symbol=eof_symbol)

        self.escape_symbol = escape_symbol
        self.eof_symbol = eof_symbol

    def encode(self, symbol, history, bits):
        start_order = min(len(history), self.model_order) if self.model_order >= 0 else -1

        current_order = start_order
        while current_order >= 0:
            context = history[len(history) - current_order:] if current_order > 0 else tuple()
            table = self.model.get_context_table(context)

            # In the current order we actually see the context, continue in the order
            if symbol in table.frequencies:
                self.coder.encode_symbol(symbol, table, bits)
                return
            else:
                # new context create reduce the order
                self.coder.encode_symbol(self.escape_symbol, table, bits)
                current_order -= 1
        if symbol == EOF():
            self.coder.encode_symbol(self.eof_symbol, self.model.get_context_table(tuple()), bits)
        else:
            self.coder.encode_symbol(symbol, self.model.order_minus_1, bits)

    def compress(self, data):
        bits = bytearray()
        history = tuple()
        for byte in data:
            self.encode(byte, history, bits)
            if self.model_order >= 0:
                self.model.update(history, byte)
                history = (history + (byte,))[-self.model_order:] if self.model_order > 0 else tuple()
        self.encode(self.eof_symbol, history, bits)
        self.coder.finish(bits)
        return bits


class PPMDecompressor:
    def __init__(self, model_order=1, eof_symbol=EOF(), escape_symbol=ESC()):
        self.model_order = model_order
        self.model = PPMModel(model_order, escape_symbol=escape_symbol, eof_symbol=eof_symbol)
        self.coder = ArithmeticCodding(precision=32, eof_symbol=eof_symbol)

        self.escape_symbol = escape_symbol
        self.eof_symbol = eof_symbol

    def decompress(self, bits):
        self.model = PPMModel(self.model_order)
        self.coder = ArithmeticCodding()
        result = bytearray()
        history = tuple()

        # Iterador para consumir bits de forma eficiente
        bit_iter = iter(bits)

        # Inicialización del registro 'code' (valor actual del intervalo)
        code = 0
        for _ in range(self.coder.precision):
            code = (code << 1) | next(bit_iter, 0)

        while True:
            # start in the max order
            current_order = min(len(history), self.model_order) if self.model_order >= 0 else -1

            while current_order >= -1:
                # select the table following the context
                if current_order >= 0:
                    ctx = history[len(history) - current_order:] if current_order > 0 else tuple()
                    table = self.model.get_context_table(ctx)
                else:
                    table = self.model.order_minus_1

                # 1. map the actual value of the symbol in the table
                range_width = self.coder.high - self.coder.low + 1
                total = table.nsymbols
                value = ((code - self.coder.low + 1) * total - 1) // range_width

                symbol = None
                for s, (r_low, r_high) in table.cumulative_ranges.items():
                    if r_low <= value < r_high:
                        symbol = s
                        # update limits of the coder
                        self.coder.high = self.coder.low + (range_width * r_high // total) - 1
                        self.coder.low = self.coder.low + (range_width * r_low // total)
                        break

                while True:
                    if self.coder.high < self.coder.half:
                        pass
                    elif self.coder.low >= self.coder.half:
                        self.coder.low -= self.coder.half
                        self.coder.high -= self.coder.half
                        code -= self.coder.half
                    elif self.coder.low >= self.coder.quarter and self.coder.high < 3 * self.coder.quarter:
                        self.coder.low -= self.coder.quarter
                        self.coder.high -= self.coder.quarter
                        code -= self.coder.quarter
                    else:
                        break

                    self.coder.low <<= 1
                    self.coder.high = (self.coder.high << 1) | 1
                    code = ((code << 1) | next(bit_iter, 0)) & self.coder.max_val

                if symbol == self.escape_symbol:
                    current_order -= 1
                else:
                    if symbol == EOF():
                        return bytes(result)

                    # save the byte and update the model
                    result.append(symbol)
                    if self.model_order >= 0:
                        self.model.update(history, symbol)
                        history = (history + (symbol,))[-self.model_order:] if self.model_order > 0 else tuple()
                    break


# --- Test ---
original = b"BANANA_BANANERA"
ppmcompresor = PPMCompressor(model_order=2)
ppmdecompresor = PPMDecompressor(model_order=2)
bits = ppmcompresor.compress(original)
decoded = ppmdecompresor.decompress(bits)

print(f"Original: {original.decode()}")
print(f"Decodificado: {decoded.decode()}")
print(f"Bits totales: {len(bits)}")
