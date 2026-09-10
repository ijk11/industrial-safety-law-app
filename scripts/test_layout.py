"""원문 글자를 보존하면서 문장과 표의 줄을 복원하는지 검사한다."""
import re
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

    def test_baked_appendix_tables_are_rows_not_lumps_or_shreds(self):
        """별표를 표로 풀 때 뭉치거나 흩어지지 않았는지 본다.

        칸막이가 없는 표는 어디서 행이 갈리는지 원문이 말해 주지 않는다. 통째로 한
        행으로 묶으면 이름과 값이 짝을 잃고, 줄마다 자르면 한 항목이 여러 줄로
        흩어져 값이 첫 줄에만 남는다. 둘 다 원문보다 읽기 나쁘다."""
        docs = json.loads(gzip.decompress((Path(ROOT) / 'web/data/laws.json.gz').read_bytes()))
        box = re.compile('[\u2500-\u257f]')
        for baked in docs:
            for table in baked.get('별표', []):
                if not table['번호'].startswith('별표'):
                    continue          # 서식은 서류 양식이라 표로 풀지 않는다
                for i, piece in enumerate(table.get('조각') or []):
                    if piece[0] != 'r':
                        continue
                    rows = [[c if isinstance(c, str) else c[0] for c in row] for row in piece[1]]
                    with self.subTest(law=baked['법령명'], table=table['번호'], piece=i):
                        self.assertGreaterEqual(max(len(r) for r in rows), 2)
                        self.assertFalse(any(box.search(c) for r in rows for c in r))
                        lines = sum(1 + c.count('\n') for r in rows for c in r[:1])
                        if lines >= 10:
                            self.assertGreater(len(rows), 2)

    def test_penalty_table_keeps_each_violation_on_one_row(self):
        """과태료 부과기준은 위반행위마다 1·2·3차 금액이 한 줄에 붙어야 한다."""
        docs = json.loads(gzip.decompress((Path(ROOT) / 'web/data/laws.json.gz').read_bytes()))
        decree = next(d for d in docs if d['법령명'] == '산업안전보건법 시행령')
        table = next(t for t in decree['별표'] if t['번호'] == '별표 35')
        rows = next(p[1] for p in table['조각'] if p[0] == 'r')
        self.assertTrue(150 <= len(rows) <= 400, len(rows))
        money = [r for r in rows if len(r) >= 6 and str(r[-1]).strip()]
        self.assertGreater(len(money), 100, len(money))

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
