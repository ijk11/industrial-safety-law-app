"""원문 글자를 보존하면서 문장과 표의 줄을 복원하는지 검사한다."""
import unittest
import collections
import gzip
import json
from pathlib import Path

from fetch_laws import soften
from build_app import ROOT, Corpus, join, blocks, is_border, split_table, collect


class LayoutTests(unittest.TestCase):
    def test_sentence_ending_is_not_item_da(self):
        source = '1. 다음 각 목과 같다.가. A를 말한다.나. B를 말한다.다. C를 말한다.2. 다른 사항'
        expected = '1. 다음 각 목과 같다.\n  가. A를 말한다.\n  나. B를 말한다.\n  다. C를 말한다.\n2. 다른 사항'
        self.assertEqual(soften(source), expected)

    def test_noun_before_next_item_is_kept(self):
        source = '1. 다음 각 목의 전원가. 격리된 전원나. 전기화학적 전원다. 고장 시의 전원2. 다른 사항'
        self.assertIn('전원\n  다. 고장', soften(source))
        self.assertIn('전원\n  나. 전기', soften(source))

    def test_printed_sentence_tail_is_not_a_new_item(self):
        self.assertEqual(join(['최소 바닥면적으로 한', '다.']), '최소 바닥면적으로 한다.')
        self.assertEqual(join(['휴게시설이라 한', '다)을 사용하는 경우']), '휴게시설이라 한다)을 사용하는 경우')
        self.assertEqual(join(['나. 축전기 등 전원', '다. 다른 전원']), '나. 축전기 등 전원\n다. 다른 전원')

    def test_short_word_requires_unbroken_source_evidence(self):
        corpus = Corpus('면적 기준. 근로자 보호. 이 목에서 정한다.')
        self.assertEqual(join(['면', '적'], corpus), '면적')
        self.assertEqual(join(['근로', '자'], corpus), '근로자')
        self.assertEqual(join(['이', '목'], corpus), '이\n목')
        self.assertEqual(join(['낯', '선'], corpus), '낯\n선')

    def test_mixed_weight_borders_and_inline_caption(self):
        self.assertTrue(is_border('┝━┯━━┿━━┥'))
        self.assertTrue(is_border('┍━━┯━━┑'))
        text = '표 제목┌──┬──┐\n│가  │나  │\n└──┴──┘다음 설명'
        kinds = [kind for kind, _ in blocks(text)]
        self.assertEqual(kinds, ['txt', 'tbl', 'txt'])
        pieces = split_table(text)
        self.assertEqual(pieces, [['t', '표 제목'], ['r', [['가', '나']]], ['t', '다음 설명']])

    def test_baked_tables_preserve_all_source_characters(self):
        docs = json.loads(gzip.decompress((Path(ROOT) / 'web/data/laws.json.gz').read_bytes()))
        def characters(text):
            return collections.Counter(c for c in text if not c.isspace() and not '\u2500' <= c <= '\u257f')
        for source, baked in zip(collect(), docs):
            for raw, table in zip(source['별표'], baked['별표']):
                text = table.get('내용', '')
                if table.get('조각'):
                    text = ''.join(p[1] if p[0] == 't' else ''.join(
                        c if isinstance(c, str) else c[0] for row in p[1] for c in row)
                        for p in table['조각'])
                with self.subTest(law=source['법령명'],table=table['번호']):
                    self.assertEqual(characters(text), characters(raw['내용']))


if __name__ == '__main__':
    unittest.main()
