import re

from openpyxl.formula import Tokenizer

text_functions = [
    "CONCATENATE",
    "CONCAT",
    "TEXTJOIN",
    "LEFT",
    "RIGHT",
    "MID",
    "LEN",
    "FIND",
    "SEARCH",
    "REPLACE",
    "SUBSTITUTE",
    "TRIM",
    "LOWER",
    "UPPER",
    "PROPER",
    "REPT",
    "TEXT",
    "VALUE",
    "CHAR",
    "CLEAN",
    "CODE"
]

official_functions = ['ABS', 'ACCRINT', 'ACCRINTM', 'ACOS', 'ACOSH', 'ACOT', 'ACOTH', 'ADDRESS', 'AGGREGATE',
                      'AMORDEGRC', 'AMORLINC', 'AND', 'ARABIC', 'AREAS', 'ASIN', 'ASINH', 'ATAN', 'ATAN2', 'ATANH',
                      'AVEDEV', 'AVERAGE', 'AVERAGEA', 'AVERAGEIF', 'AVERAGEIFS', 'BAHTTEXT', 'BASE', 'BESSELI',
                      'BESSELJ', 'BESSELK', 'BESSELY', 'BETA.DIST', 'BETA.INV', 'BETADIST', 'BETAINV', 'BIN2DEC',
                      'BIN2HEX', 'BIN2OCT', 'BINOM.DIST', 'BINOM.DIST.RANGE', 'BINOM.INV', 'BINOMDIST', 'BITAND',
                      'BITLSHIFT', 'BITOR', 'BITRSHIFT', 'BITXOR', 'CEILING', 'CEILING.MATH', 'CEILING.PRECISE', 'CELL',
                      'CHAR', 'CHIDIST', 'CHIINV', 'CHISQ.DIST', 'CHISQ.DIST.RT', 'CHISQ.INV', 'CHISQ.INV.RT',
                      'CHISQ.TEST', 'CHITEST', 'CHOOSE', 'CODE', 'COLUMN', 'COLUMNS', 'COMBIN', 'COMBINA', 'COMPLEX',
                      'CONCAT', 'CONCATENATE', 'CONFIDENCE', 'CONFIDENCE.NORM', 'CONFIDENCE.T', 'CONVERT', 'CORREL',
                      'COS', 'COSH', 'COT', 'COTH', 'COUNT', 'COUNTA', 'COUNTBLANK', 'COUNTIF', 'COUNTIFS', 'COUPDAYBS',
                      'COUPDAYS', 'COUPDAYSNC', 'COUPNCD', 'COUPNUM', 'COUPPCD', 'COVAR', 'COVARIANCE.P',
                      'COVARIANCE.S',
                      'CRITBINOM', 'CSC', 'CSCH', 'CUBEKPIMEMBER', 'CUBEMEMBER', 'CUBEMEMBERPROPERTY',
                      'CUBERANKEDMEMBER', 'CUBESET', 'CUBESETCOUNT', 'CUBEVALUE', 'CUMIPMT', 'CUMPRINC', 'DATE',
                      'DATEVALUE', 'DAVERAGE', 'DAY', 'DAYS', 'DAYS360', 'DB', 'DCOUNT', 'DCOUNTA', 'DDB', 'DEC2BIN',
                      'DEC2HEX', 'DEC2OCT', 'DECIMAL', 'DEGREES', 'DELTA', 'DEVSQ', 'DGET', 'DISC', 'DMAX', 'DMIN',
                      'DOLLAR', 'DOLLARDE', 'DOLLARFR', 'DPRODUCT', 'DSTDEV', 'DSTDEVP', 'DSUM', 'DURATION', 'DVAR',
                      'DVARP', 'EDATE', 'EFFECT', 'ENCODEURL', 'EOMONTH', 'ERF', 'ERF.PRECISE', 'ERFC', 'ERFC.PRECISE',
                      'ERROR.TYPE', 'EVEN', 'EXACT', 'EXP', 'EXPON.DIST', 'EXPONDIST', 'F.DIST', 'F.DIST.RT', 'F.INV',
                      'F.INV.RT', 'F.TEST', 'FACT', 'FACTDOUBLE', 'FDIST', 'FILTERXML', 'FIND', 'FINV', 'FISHER',
                      'FISHERINV', 'FIXED', 'FLOOR', 'FLOOR.MATH', 'FLOOR.PRECISE', 'FORECAST', 'FORECAST.ETS',
                      'FORECAST.ETS.CONFINT', 'FORECAST.ETS.SEASONALITY', 'FORECAST.ETS.STAT', 'FORECAST.LINEAR',
                      'FORMULATEXT', 'FREQUENCY', 'FTEST', 'FV', 'FVSCHEDULE', 'GAMMA', 'GAMMA.DIST', 'GAMMA.INV',
                      'GAMMADIST', 'GAMMAINV', 'GAMMALN', 'GAMMALN.PRECISE', 'GAUSS', 'GCD', 'GEOMEAN', 'GESTEP',
                      'GETPIVOTDATA', 'GROWTH', 'HARMEAN', 'HEX2BIN', 'HEX2DEC', 'HEX2OCT', 'HLOOKUP', 'HOUR',
                      'HYPERLINK', 'HYPGEOM.DIST', 'HYPGEOMDIST', 'IF', 'IFERROR', 'IFNA', 'IFS', 'IMABS', 'IMAGINARY',
                      'IMARGUMENT', 'IMCONJUGATE', 'IMCOS', 'IMCOSH', 'IMCOT', 'IMCSC', 'IMCSCH', 'IMDIV', 'IMEXP',
                      'IMLN', 'IMLOG10', 'IMLOG2', 'IMPOWER', 'IMPRODUCT', 'IMREAL', 'IMSEC', 'IMSECH', 'IMSIN',
                      'IMSINH', 'IMSQRT', 'IMSUB', 'IMSUM', 'IMTAN', 'INDEX', 'INDIRECT', 'INFO', 'INT', 'INTERCEPT',
                      'INTRATE', 'IPMT', 'IRR', 'ISBLANK', 'ISERR', 'ISERROR', 'ISEVEN', 'ISFORMULA', 'ISLOGICAL',
                      'ISNA', 'ISNONTEXT', 'ISNUMBER', 'ISO.CEILING', 'ISODD', 'ISOWEEKNUM', 'ISPMT', 'ISREF', 'ISTEXT',
                      'KURT', 'LARGE', 'LCM', 'LEFT', 'LEN', 'LINEST', 'LN', 'LOG', 'LOG10', 'LOGEST', 'LOGINV',
                      'LOGNORM.DIST', 'LOGNORM.INV', 'LOGNORMDIST', 'LOOKUP', 'LOWER', 'MATCH', 'MAX', 'MAXA', 'MAXIFS',
                      'MDETERM', 'MDURATION', 'MEDIAN', 'MID', 'MIN', 'MINA', 'MINIFS', 'MINUTE', 'MINVERSE', 'MIRR',
                      'MMULT', 'MOD', 'MODE', 'MODE.MULT', 'MODE.SNGL', 'MONTH', 'MROUND', 'MULTINOMIAL', 'MUNIT', 'N',
                      'NA', 'NEGBINOM.DIST', 'NEGBINOMDIST', 'NETWORKDAYS', 'NETWORKDAYS.INTL', 'NOMINAL', 'NORM.DIST',
                      'NORM.INV', 'NORM.S.DIST', 'NORM.S.INV', 'NORMDIST', 'NORMINV', 'NORMSDIST', 'NORMSINV', 'NOT',
                      'NOW', 'NPER', 'NPV', 'NUMBERVALUE', 'OCT2BIN', 'OCT2DEC', 'OCT2HEX', 'ODD', 'ODDFPRICE',
                      'ODDFYIELD', 'ODDLPRICE', 'ODDLYIELD', 'OFFSET', 'OR', 'PDURATION', 'PEARSON', 'PERCENTILE',
                      'PERCENTILE.EXC', 'PERCENTILE.INC', 'PERCENTRANK', 'PERCENTRANK.EXC', 'PERCENTRANK.INC', 'PERMUT',
                      'PERMUTATIONA', 'PHI', 'PI', 'PMT', 'POISSON', 'POISSON.DIST', 'POWER', 'PPMT', 'PRICE',
                      'PRICEDISC', 'PRICEMAT', 'PROB', 'PRODUCT', 'PROPER', 'PV', 'QUARTILE', 'QUARTILE.EXC',
                      'QUARTILE.INC', 'QUOTIENT', 'RADIANS', 'RAND', 'RANDBETWEEN', 'RANK', 'RANK.AVG', 'RANK.EQ',
                      'RATE', 'RECEIVED', 'REPLACE', 'REPT', 'RIGHT', 'ROMAN', 'ROUND', 'ROUNDDOWN', 'ROUNDUP', 'ROW',
                      'ROWS', 'RRI', 'RSQ', 'RTD', 'SEARCH', 'SEC', 'SECH', 'SECOND', 'SERIESSUM', 'SHEET', 'SHEETS',
                      'SIGN', 'SIN', 'SINH', 'SKEW', 'SKEW.P', 'SLN', 'SLOPE', 'SMALL', 'SQRT', 'SQRTPI', 'STANDARDIZE',
                      'STDEV', 'STDEV.P', 'STDEV.S', 'STDEVA', 'STDEVP', 'STDEVPA', 'STEYX', 'SUBSTITUTE', 'SUBTOTAL',
                      'SUM', 'SUMIF', 'SUMIFS', 'SUMPRODUCT', 'SUMSQ', 'SUMX2MY2', 'SUMX2PY2', 'SUMXMY2', 'SWITCH',
                      'SYD', 'T', 'T.DIST', 'T.DIST.2T', 'T.DIST.RT', 'T.INV', 'T.INV.2T', 'T.TEST', 'TAN', 'TANH',
                      'TBILLEQ', 'TBILLPRICE', 'TBILLYIELD', 'TDIST', 'TEXT', 'TEXTJOIN', 'TIME', 'TIMEVALUE', 'TINV',
                      'TODAY', 'TRANSPOSE', 'TREND', 'TRIM', 'TRIMMEAN', 'TRUNC', 'TTEST', 'TYPE', 'UNICHAR', 'UNICODE',
                      'UPPER', 'VALUE', 'VAR', 'VAR.P', 'VAR.S', 'VARA', 'VARP', 'VARPA', 'VDB', 'VLOOKUP',
                      'WEBSERVICE',
                      'WEEKDAY', 'WEEKNUM', 'WEIBULL', 'WEIBULL.DIST', 'WORKDAY', 'WORKDAY.INTL', 'XIRR', 'XNPV', 'XOR',
                      'YEAR', 'YEARFRAC', 'YIELD', 'YIELDDISC', 'YIELDMAT', 'Z.TEST', 'ZTEST', 'FALSE', 'TRUE']


def tokenize_formula(formula):
    """
    Tokenize a formula and return a list of tuples, each containing the token value, type, and subtype.

    Parameters:
    formula (str): The formula to tokenize.

    Returns:
    list: A list of tuples, each containing the token value, type, and subtype.
    """
    tok = Tokenizer(formula)
    return [(t.value, t.type, t.subtype) for t in tok.items]


def validate_token(token):
    """
    Validate a token from a formula. Raises a ValueError if the token is invalid.

    Parameters:
    token (tuple): The token to validate, as a tuple containing the token value, type, and subtype.

    Raises:
    ValueError: If the token is invalid.
    """
    t_value, t_type, t_subtype = token

    valid_functions = ['ACOS', 'ACOSH', 'AND', 'ASIN', 'ATAN', 'AVERAGE', 'AVERAGEA', 'BINOMDIST', 'CEILING', 'CELL',
                       'CHAR', 'CHIDIST', 'CHIINV', 'CHOOSE', 'COLUMN', 'COMBIN', 'CONCATENATE', 'CONFIDENCE', 'CORREL',
                       'COS', 'COSH', 'COUNT', 'COUNTA', 'COUNTBLANK', 'COUNTIF', 'COUNTIFS', 'COVAR', 'DATE',
                       'DATEDIF', 'DATEVALUE', 'DAY', 'DEGREES', 'DOLLAR', 'EDATE', 'EOMONTH', 'ERFC', 'EVEN', 'EXACT',
                       'EXP', 'FACT', 'FIND', 'FIXED', 'FLOOR', 'FORECAST', 'FREQUENCY', 'FV', 'GAMMADIST', 'GEOMEAN',
                       'HLOOKUP', 'HOUR', 'HYPERLINK', 'IF', 'IFERROR', 'INDEX', 'INDIRECT', 'INT', 'INTERCEPT', 'IRR',
                       'ISBLANK', 'ISERR', 'ISERROR', 'ISNA', 'ISNUMBER', 'ISTEXT', 'LARGE', 'LEFT', 'LEN', 'LINEST',
                       'LN', 'LOG', 'LOG10', 'LOGEST', 'LOOKUP', 'LOWER', 'MATCH', 'MAX', 'MAXA', 'MDETERM', 'MEDIAN',
                       'MID', 'MIN', 'MINA', 'MINUTE', 'MINVERSE', 'MMULT', 'MOD', 'MODE', 'MONTH', 'MROUND', 'N',
                       'NETWORKDAYS', 'NORMDIST', 'NORMINV', 'NORMSDIST', 'NORMSINV', 'NOT', 'NOW', 'NPV', 'OFFSET',
                       'OR', 'PI', 'PMT', 'POWER', 'PRODUCT', 'PROPER', 'PV', 'QUARTILE', 'QUOTIENT', 'RADIANS', 'RAND',
                       'RANK', 'REPT', 'RIGHT', 'ROUND', 'ROUNDDOWN', 'ROUNDUP', 'ROW', 'ROWS', 'SEARCH', 'SIGN', 'SIN',
                       'SLOPE', 'SMALL', 'SQRT', 'STDEV', 'STDEVA', 'STDEVP', 'SUBNM', 'SUBSTITUTE', 'SUBTOTAL', 'SUM',
                       'SUMIF', 'SUMPRODUCT', 'SUMSQ', 'TANH', 'TDIST', 'TEXT', 'TIME', 'TINV', 'TODAY', 'TRANSPOSE',
                       'TRIM', 'TRUE', 'TRUNC', 'TTEST', 'UPPER', 'VAR', 'VARA', 'VARP', 'VLOOKUP', 'WEEKDAY', 'XIRR',
                       'XNPV', 'YEAR']

    if t_type == 'OPERAND' and t_subtype == 'ERROR':
        raise ValueError(f"Invalid token value: {t_value}")

    if t_type == 'FUNC' and t_subtype == 'OPEN':
        if not t_value.endswith('('):
            raise ValueError(f"Invalid function syntax: {t_value}")
        func_name = t_value[:-1]  # Remove the trailing '('
        if not func_name in valid_functions:
            raise ValueError(f"Function name is not in valid formulas: {func_name}")

    if t_type == 'OPERAND' and t_subtype == 'RANGE':
        clean_range = t_value.split('!')[-1].replace('$', '')
        if not re.match(r"[A-Z]+[0-9]+(:[A-Z]+[0-9]+)?", clean_range):
            raise ValueError(f"Invalid range format: {t_value}")


def parse_formula(formula):
    """
    Parse a formula and return a list of tuples, each containing the token value, type, and subtype.
    Raises a ValueError if an error token is encountered.

    Parameters:
    formula (str): The formula to parse.

    Returns:
    list: A list of tuples, each containing the token value, type, and subtype.

    Raises:
    ValueError: If an error token is found in the formula.
    """
    tokens = tokenize_formula(formula)
    for token in tokens:
        validate_token(token)
    return tokens


def get_formula_pattern(formula):
    """
    Get the pattern of a formula.
    The pattern is defined as the sorted list of function names in the formula.

    Parameters:
    formula (str): The formula to get the pattern from.

    Returns:
    str: The pattern of the formula.

    Raises:
    ValueError: If an error token is found in the formula.
    """
    parsed_formula = parse_formula(formula)
    func_names = [t_value.rstrip('(') for t_value, t_type, t_subtype in parsed_formula if
                  t_type == 'FUNC' and t_subtype == 'OPEN']
    pattern = ','.join(sorted(func_names))
    return pattern


def validate_range(range_str, sheet_name):
    if '!' in range_str:
        range_sheet = range_str.split('!')[0].strip("'")
        if range_sheet != sheet_name:
            raise ValueError(f"Range refers to another sheet. Current sheet: {sheet_name}, range: {range_str}")
    clean_range = range_str.split('!')[-1].replace('$', '')
    if not re.match(r"[A-Z]+[0-9]+(:[A-Z]+[0-9]+)?", clean_range):
        raise ValueError(f"Invalid range format: {range_str}")
    return clean_range


def extract_range_from_formula(formula, sheet_name):
    parsed_formula = parse_formula(formula)
    ranges = [t[0] for t in parsed_formula if t[1] == 'OPERAND' and t[2] == 'RANGE']
    valid_ranges = []
    for r in ranges:
        try:
            clean_valid_range = validate_range(r, sheet_name)
            valid_ranges.append(clean_valid_range)
        except ValueError as e:
            print(f"Invalid range found: {e}")
    return list(set(valid_ranges))


def check_formula_validity(formula, sheet_name):
    functions = [
        "CONCATENATE",
        "CONCAT",
        "TEXTJOIN",
        "LEFT",
        "RIGHT",
        "MID",
        "LEN",
        "FIND",
        "SEARCH",
        "REPLACE",
        "SUBSTITUTE",
        "TRIM",
        "LOWER",
        "UPPER",
        "PROPER",
        "REPT",
        "TEXT",
        "VALUE",
        "CHAR",
        "CLEAN",
        "CODE"
    ]
    parsed_formula = parse_formula(formula)
    func_names = [t_value.rstrip('(') for t_value, t_type, t_subtype in parsed_formula if
                  t_type == 'FUNC' and t_subtype == 'OPEN']
    range_errors = extract_range_from_formula(formula, sheet_name)

    if len(func_names) > 3:
        raise ValueError("More than 3 functions in formula")
    elif len(formula) > 60:
        raise ValueError("Formula length greater than 50")
    elif len(func_names) == 1 and func_names[0] in functions and len(range_errors) > 0:
        raise ValueError("Only string operations and no range")
    elif len(range_errors) > 0:
        raise ValueError(f"Range errors: {range_errors}")

    return None


if __name__ == '__main__':
    print(parse_formula('=VLOOKUP(I46,I57,2,FALSE)'))
    print(parse_formula('=SUM(B2:B3)'))
    print(tokenize_formula("=SERIES(\"Number of Programs\",'D:\\COMMERCIAL PROGRAMS\\Program Summaries\\[Historical Trend of Comm Kitchens Programs.xls]Overall'!$A$4:$A$12,Overall2004to2012!$B$5:$B$13,1)"))

