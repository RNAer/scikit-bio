#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2013--, scikit-bio development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import os
from unittest import TestCase, main

from future.utils.six import StringIO
from numpy import arange, array

from skbio.parse.sequences import (SequenceIterator, FastaIterator,
                                   FastqIterator, load)


class SeqIterTests(TestCase):
    def setUp(self):
        self.seq_ok = {'SequenceID': 'foo',
                       'Sequence': 'AATTGGCC',
                       'QualID': None,
                       'Qual': None}

        self.seqqual_ok = {'SequenceID': 'foo',
                           'Sequence': 'AATTGGCC',
                           'QualID': 'foo',
                           'Qual': arange(8)}

        self.seq_bad = {'SequenceID': 'foo',
                        'Sequence': 'AATT  GGCC',
                        'QualID': None,
                        'Qual': None}

        self.seqqual_bad_id = {'SequenceID': 'foo',
                               'Sequence': 'AATTGGCC',
                               'QualID': 'bar',
                               'Qual': arange(8)}

        self.seqqual_bad_qual = {'SequenceID': 'foo',
                                 'Sequence': 'AATTGGCC',
                                 'QualID': 'foo',
                                 'Qual': arange(5)}

        def rev_f(st):
            st['Sequence'] = st['Sequence'][::-1]
            st['Qual'] = st['Qual'][::-1] if st['Qual'] is not None else None

        self.rev_f = rev_f

    def test_validate_ids_true(self):
        wk = SequenceIterator(['aattgg'], valid_id=True)

        wk.state = self.seq_ok.copy()
        wk.validate_ids()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_ok.copy()
        wk.validate_ids()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_bad_id.copy()
        wk.validate_ids()
        self.assertTrue(wk.failed)

    def test_validate_ids_false(self):
        wk = SequenceIterator(['aattgg'], valid_id=False)

        wk.state = self.seq_ok.copy()
        wk.validate_ids()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_ok.copy()
        wk.validate_ids()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_bad_id.copy()
        wk.validate_ids()
        self.assertFalse(wk.failed)

    def test_validate_lengths_true(self):
        wk = SequenceIterator(['aattgg'], valid_length=True)

        wk.state = self.seq_ok.copy()
        wk.valid_lengths()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_ok.copy()
        wk.valid_lengths()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_bad_qual.copy()
        wk.valid_lengths()
        self.assertTrue(wk.failed)

    def test_validate_lengths_false(self):
        wk = SequenceIterator(['aattgg'], valid_length=False)

        wk.state = self.seq_ok.copy()
        wk.valid_lengths()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_ok.copy()
        wk.valid_lengths()
        self.assertFalse(wk.failed)

        wk.state = self.seqqual_bad_qual.copy()
        wk.valid_lengths()
        self.assertFalse(wk.failed)

    def test_transform(self):
        wk = SequenceIterator(['aattgg'], transform=self.rev_f)

        wk.state = self.seqqual_ok.copy()
        self.assertEqual(wk.state['Sequence'], self.seqqual_ok['Sequence'])
        wk.transform()
        self.assertEqual(wk.state['Sequence'],
                         self.seqqual_ok['Sequence'][::-1])
        self.assertTrue((wk.state['Qual'] ==
                         self.seqqual_ok['Qual'][::-1]).all())


class FastaTests(TestCase):
    def setUp(self):
        self.fastas = [StringIO(fasta1), StringIO(fasta2), StringIO(fasta3)]
        self.quals = [StringIO(qual1), StringIO(qual2), StringIO(qual3)]

        self.bad_qual_val = [StringIO(qual1), StringIO(qual_bad_val),
                             StringIO(qual3)]
        self.bad_qual_id = [StringIO(qual1), StringIO(qual_bad_id),
                            StringIO(qual3)]

    def test_fasta_gen(self):
        wk = FastaIterator(seq=self.fastas)
        gen = wk()

        exp1 = {'SequenceID': '1', 'Sequence': 'aattggcc', 'Qual': None,
                'QualID': None}
        exp2 = {'SequenceID': '2', 'Sequence': 'aattaatt', 'Qual': None,
                'QualID': None}
        exp3 = {'SequenceID': '3', 'Sequence': 'atat', 'Qual': None,
                'QualID': None}
        exp4 = {'SequenceID': '4', 'Sequence': 'attatt', 'Qual': None,
                'QualID': None}
        exp5 = {'SequenceID': '5', 'Sequence': 'ggccc', 'Qual': None,
                'QualID': None}

        obs1 = next(gen)
        self.assertEqual(obs1, exp1)
        self.assertFalse(wk.failed)

        obs2 = next(gen)
        self.assertEqual(obs2, exp2)
        self.assertFalse(wk.failed)

        obs3 = next(gen)
        self.assertEqual(obs3, exp3)
        self.assertFalse(wk.failed)

        obs4 = next(gen)
        self.assertEqual(obs4, exp4)
        self.assertFalse(wk.failed)

        obs5 = next(gen)
        self.assertEqual(obs5, exp5)
        self.assertFalse(wk.failed)

    def test_fasta_qual(self):
        wk = FastaIterator(seq=self.fastas, qual=self.quals)
        gen = wk()

        exp1 = {'SequenceID': '1', 'Sequence': 'aattggcc',
                'Qual': arange(1, 9), 'QualID': '1'}
        exp2 = {'SequenceID': '2', 'Sequence': 'aattaatt', 'QualID': '2',
                'Qual': arange(1, 9)[::-1]}
        exp3 = {'SequenceID': '3', 'Sequence': 'atat', 'Qual': arange(1, 5),
                'QualID': '3'}
        exp4 = {'SequenceID': '4', 'Sequence': 'attatt', 'Qual': arange(1, 7),
                'QualID': '4'}
        exp5 = {'SequenceID': '5', 'Sequence': 'ggccc', 'Qual': arange(1, 6),
                'QualID': '5'}

        obs1 = next(gen)
        self.assertTrue((obs1['Qual'] == exp1['Qual']).all())
        obs1.pop('Qual')
        exp1.pop('Qual')
        self.assertEqual(obs1, exp1)
        self.assertFalse(wk.failed)

        obs2 = next(gen)
        self.assertTrue((obs2['Qual'] == exp2['Qual']).all())
        obs2.pop('Qual')
        exp2.pop('Qual')
        self.assertEqual(obs2, exp2)
        self.assertFalse(wk.failed)

        obs3 = next(gen)
        self.assertTrue((obs3['Qual'] == exp3['Qual']).all())
        obs3.pop('Qual')
        exp3.pop('Qual')
        self.assertEqual(obs3, exp3)
        self.assertFalse(wk.failed)

        obs4 = next(gen)
        self.assertTrue((obs4['Qual'] == exp4['Qual']).all())
        obs4.pop('Qual')
        exp4.pop('Qual')
        self.assertEqual(obs4, exp4)
        self.assertFalse(wk.failed)

        obs5 = next(gen)
        self.assertTrue((obs5['Qual'] == exp5['Qual']).all())
        obs5.pop('Qual')
        exp5.pop('Qual')
        self.assertEqual(obs5, exp5)
        self.assertFalse(wk.failed)

    def test_fasta_badqual_val(self):
        wk = FastaIterator(seq=self.fastas, qual=self.bad_qual_val)
        gen = wk()

        # default behavior is to sliently ignore
        exp_ids = ['1', '2', '4', '5']
        obs_ids = [r['SequenceID'] for r in gen]

        self.assertEqual(obs_ids, exp_ids)

    def test_fasta_badqual_id(self):
        wk = FastaIterator(seq=self.fastas, qual=self.bad_qual_id)
        gen = wk()

        # default behavior is to sliently ignore
        exp_ids = ['1', '2', '4', '5']
        obs_ids = [r['SequenceID'] for r in gen]

        self.assertEqual(obs_ids, exp_ids)


class FastqTests(TestCase):
    def setUp(self):
        self.fastqs = [StringIO(fastq1), StringIO(fastq2)]

    def test_fastq_gen(self):
        wk = FastqIterator(seq=self.fastqs)
        gen = wk()

        exp1 = {'SequenceID': '1', 'Sequence': 'atat', 'QualID': '1',
                'Qual': array([32, 33, 34, 35])}
        exp2 = {'SequenceID': '2', 'Sequence': 'atgc', 'QualID': '2',
                'Qual': array([33, 34, 35, 36])}
        exp3 = {'SequenceID': '3', 'Sequence': 'taa', 'QualID': '3',
                'Qual': array([36, 37, 38])}

        obs1 = next(gen)
        self.assertTrue((obs1['Qual'] == exp1['Qual']).all())
        obs1.pop('Qual')
        exp1.pop('Qual')
        self.assertEqual(obs1, exp1)

        obs2 = next(gen)
        self.assertTrue((obs2['Qual'] == exp2['Qual']).all())
        obs2.pop('Qual')
        exp2.pop('Qual')
        self.assertEqual(obs2, exp2)

        obs3 = next(gen)
        self.assertTrue((obs3['Qual'] == exp3['Qual']).all())
        obs3.pop('Qual')
        exp3.pop('Qual')
        self.assertEqual(obs3, exp3)


# copied from maths/stats/ordination/tests/test_ordination.py
def get_data_path(fn):
    """Return path to filename `fn` in the data folder."""
    path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(path, 'data', fn)
    return data_path


class SequenceLoadTests(TestCase):
    def setUp(self):
        self.fna1 = get_data_path('fna1.fasta')
        self.fna1gz = get_data_path('fna1.fna.gz')
        self.fq1 = get_data_path('fq1.fq')
        self.fq1gz = get_data_path('fq1.fastq.gz')
        self.qual1 = get_data_path('fna1.qual')
        self.noext = get_data_path('noextensionfasta')

    def test_single_files(self):
        """load should handle a single file, and can be gzipped"""
        it = load(self.fna1)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': None, 'Qual': None},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': None, 'Qual': None}]
        self.assertEqual(obs, exp)
        it = load(self.fq1, phred_offset=64)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': 's1', 'Qual': array([40, 40, 40, 40])},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': 's2', 'Qual': array([39, 39, 39, 39, 40, 40])}]
        for o, e in zip(obs, exp):
            self.assertEqual(o['Sequence'], e['Sequence'])
            self.assertEqual(o['SequenceID'], e['SequenceID'])
            self.assertEqual(o['QualID'], e['QualID'])
            self.assertTrue((o['Qual'] == e['Qual']).all())

        it = load(self.fna1gz)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': None, 'Qual': None},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': None, 'Qual': None}]
        self.assertEqual(obs, exp)

        it = load(self.fq1gz, phred_offset=64)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': 's1', 'Qual': array([40, 40, 40, 40])},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': 's2', 'Qual': array([39, 39, 39, 39, 40, 40])}]
        for o, e in zip(obs, exp):
            self.assertEqual(o['Sequence'], e['Sequence'])
            self.assertEqual(o['SequenceID'], e['SequenceID'])
            self.assertEqual(o['QualID'], e['QualID'])
            self.assertTrue((o['Qual'] == e['Qual']).all())

    def test_multiple_files(self):
        """load should handle multiple files of different types"""
        it = load([self.fq1, self.fna1], phred_offset=64)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': 's1', 'Qual': array([40, 40, 40, 40])},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': 's2', 'Qual': array([39, 39, 39, 39, 40, 40])},
               {'Sequence': 'ATGC', 'SequenceID': 's1',
                'QualID': None, 'Qual': None},
               {'Sequence': 'AATTGG', 'SequenceID': 's2',
                'QualID': None, 'Qual': None}]

        o = obs[0]
        e = exp[0]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertTrue((o['Qual'] == e['Qual']).all())

        o = obs[1]
        e = exp[1]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertTrue((o['Qual'] == e['Qual']).all())

        o = obs[2]
        e = exp[2]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertEqual(o['Qual'], e['Qual'])

        o = obs[3]
        e = exp[3]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertEqual(o['Qual'], e['Qual'])

    def test_transform(self):
        """load should pass transform methods to the iterators"""
        def rev_f(st):
            st['Sequence'] = st['Sequence'][::-1]
            st['Qual'] = st['Qual'][::-1] if st['Qual'] is not None else None

        it = load([self.fq1gz, self.fna1], transform=rev_f, phred_offset=64)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'CGTA', 'SequenceID': 's1',
                'QualID': 's1', 'Qual': array([40, 40, 40, 40])},
               {'Sequence': 'GGTTAA', 'SequenceID': 's2',
                'QualID': 's2', 'Qual': array([40, 40, 39, 39, 39, 39])},
               {'Sequence': 'CGTA', 'SequenceID': 's1',
                'QualID': None, 'Qual': None},
               {'Sequence': 'GGTTAA', 'SequenceID': 's2',
                'QualID': None, 'Qual': None}]

        o = obs[0]
        e = exp[0]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertTrue((o['Qual'] == e['Qual']).all())

        o = obs[1]
        e = exp[1]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertTrue((o['Qual'] == e['Qual']).all())

        o = obs[2]
        e = exp[2]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertEqual(o['Qual'], e['Qual'])

        o = obs[3]
        e = exp[3]
        self.assertEqual(o['Sequence'], e['Sequence'])
        self.assertEqual(o['SequenceID'], e['SequenceID'])
        self.assertEqual(o['QualID'], e['QualID'])
        self.assertEqual(o['Qual'], e['Qual'])

    def test_force_constructor(self):
        it = load([self.noext], constructor=FastaIterator)
        obs = [rec.copy() for rec in it]
        exp = [{'Sequence': 'AATTGG', 'SequenceID': 'seq1',
                'Qual': None, 'QualID': None},
               {'Sequence': 'ATATA', 'SequenceID': 'seq2',
                'Qual': None, 'QualID': None}]
        self.assertEqual(obs, exp)


fasta1 = """>1
aattggcc
>2
aattaatt
"""

fasta2 = """>3
atat
"""

fasta3 = """>4
attatt
>5
ggccc
"""

qual1 = """>1
1 2 3 4 5 6 7 8
>2
8 7 6 5 4 3 2 1
"""

qual2 = """>3
1 2 3 4
"""

qual3 = """>4
1 2 3 4 5 6
>5
1 2 3 4 5
"""

qual_bad_val = """>3
1 2
"""

qual_bad_id = """>asdasd
1 2 3 4
"""

fastq1 = """@1
atat
+
ABCD
@2
atgc
+
BCDE
"""

fastq2 = """@3
taa
+
EFG
"""


if __name__ == '__main__':
    main()
