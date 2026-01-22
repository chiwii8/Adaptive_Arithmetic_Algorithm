try:
    from FrequencyTable import FrequencyTable, build_default_FrequencyTable, EOF
except ImportError:
    from .FrequencyTable import FrequencyTable, build_default_FrequencyTable, EOF


class ArithmeticCodding:
    def __init__(self, precision=32, eof_symbol=EOF()):
        self.precision = precision
        self.max_val = (1 << precision) - 1
        self.half = 1 << (precision - 1)
        self.quarter = self.half >> 1

        self.high = self.max_val
        self.low = 0
        self.pending = 0

        self.eof_symbol = eof_symbol

    # Copy the resultant bit of (1 - bit) for all pending bits
    def _emit(self, bit, bits):
        # set the first bit used (1 or 0)
        bits.append(bit)
        for _ in range(self.pending):
            # if bit 1 then pending bits 0(1 - 1)
            # if bit 0 then pending bits 1(1 - 0)
            bits.append(1 - bit)
        self.pending = 0

    def finish(self, bits):
        self.pending += 1
        if self.low < self.quarter:
            self._emit(0, bits)
        else:
            self._emit(1, bits)

    def encode_symbol(self, symbol, table, bits):
        total = table.nsymbols

        r_low, r_high = table.cumulative_ranges[symbol]
        range_width = self.high - self.low + 1

        self.high = self.low + (range_width * r_high // total) - 1
        self.low = self.low + (range_width * r_low // total)

        while True:
            if self.high < self.half:
                self._emit(0, bits)
            elif self.low >= self.half:
                self._emit(1, bits)
                self.low -= self.half
                self.high -= self.half
            elif self.low >= self.quarter and self.high < 3 * self.quarter:
                self.pending += 1
                self.low -= self.quarter
                self.high -= self.quarter
            else:
                break

            self.low <<= 1
            self.high = (self.high << 1) | 1

    def decode(self, bits, table, result):
        code = 0
        total = table.nsymbols
        low, high = self.low, self.high
        bit_iter = iter(bits)

        for _ in range(self.precision):
            code = (code << 1) | next(bit_iter, 0)

        while True:
            range_width = high - low + 1
            value = ((code - low + 1) * total - 1) // range_width

            for s, (r_low, r_high) in table.cumulative_ranges.items():
                if r_low <= value < r_high:
                    if s == self.eof_symbol:
                        return
                    result.append(s)
                    high = low + (range_width * r_high // total) - 1
                    low = low + (range_width * r_low // total)

                    table.updateFreqs(s)
                    total = table.nsymbols
                    break

            while True:
                if high < self.half:
                    pass
                elif low >= self.half:
                    low -= self.half
                    high -= self.half
                    code -= self.half
                elif low >= self.quarter and high < 3 * self.quarter:
                    low -= self.quarter
                    high -= self.quarter
                    code -= self.quarter
                else:
                    break

                low <<= 1
                high = (high << 1) | 1
                code = (code << 1) | next(bit_iter, 0)

                self.low = low
                self.high = high


# Helpers
def _encode(message):
    table_enc = build_default_FrequencyTable()
    coder = ArithmeticCodding(precision=32)

    bits = []

    for symbol in message:
        coder.encode_symbol(symbol, table_enc, bits)
        table_enc.updateFreqs(symbol)

    coder.finish(bits)

    print("Bits codificados:")
    print(bits)
    return bits


def _decode(bits):
    table_dec = build_default_FrequencyTable()
    decoder = ArithmeticCodding(precision=32)
    result = []
    decoder.decode(bits, table_dec, result)

    print("Símbolos decodificados:")

    decoded_text = bytes(result).decode("utf-8")
    print("result:")
    print(decoded_text)


if __name__ == "__main__":
    text = "This is an example of Arith Adaptive"
    message = list(text.encode("utf-8"))
    message.append(EOF())

    bits = _encode(message)
    _decode(bits)