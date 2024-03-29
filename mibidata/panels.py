"""Utility for working with panels saved as CSV files.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import numpy as np
import pandas as pd
from pandas.errors import ParserError
from mibidata import util


def read_csv(path):
    """Reads a panel CSV file into a dataframe.

    Args:
        path: The path to the CSV file.

    Returns:
        A dataframe containing columns 'Mass' and 'Target'.
    """
    try:
        # First try if the CSV is simply Mass,Target,
        df = pd.read_csv(path, encoding='utf-8')
        # CSV may parse successfully but not have proper columns
        if not {'Mass', 'Target'}.issubset(set(df.columns)):
            raise ParserError
        return merge_masses(df)
    except ParserError:
        # Determine lines that indicate a table header line
        header_lines = []
        with open(path, 'rt', encoding='utf-8') as f:
            line_pos = 0
            for line in f:
                if 'Mass' in line and 'Target' in line:
                    header_lines.append(line_pos)
                line_pos += 1

        last_line = line_pos

        # Determine start and end lines for each batch in file
        df = []
        for i, start in enumerate(header_lines):
            try:
                # Two blank lines and 4 lines of info between
                # batches in multi-batch CSV
                end = header_lines[i + 1] - 5
            except IndexError:
                end = last_line

            batch = pd.read_csv(path, skiprows=start,
                                skipfooter=(last_line - end),
                                engine='python',
                                encoding='utf-8')[['Mass', 'Target']]

            # Remove empty rows if they exist
            df.append(batch.dropna())

        # Combine and convert 'Mass' column to int
        combined = pd.concat(df, ignore_index=True)
        combined['Mass'] = combined['Mass'].astype(np.int64)
        combined['Target'] = combined['Target'].astype(str)
        return merge_masses(combined)


def merge_masses(df):
    """Merges 'Target' cells of a DataFrame with the same 'Mass' value.

    This function merges multiple targets that are conjugated to the same mass
    tag such that the returned DataFrame contains only unique masses. Target
    names are combined using the conventions of :func:'util.natural_sort()'.

    Args:
        df: A DataFrame of the panel containing columns 'Mass' and
            'Target'.

    Returns:
        A DataFrame containing columns 'Mass' and 'Target' with merged targets
        of the same mass.
    """
    conjugates = {}
    target_list = []
    for conj in df.to_dict(orient='records'):
        mass = conj['Mass']
        target = conj['Target']
        if conjugates.get(mass):
            conjugates[mass].append(target)
        else:
            conjugates[mass] = [target]
    for mass in conjugates:
        target_list = conjugates[mass]
        util.natural_sort(target_list)
        conjugates[mass] = ', '.join(target_list)
    return pd.DataFrame(list(conjugates.items()), columns=['Mass', 'Target'])
