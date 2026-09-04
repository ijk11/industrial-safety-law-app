"""잘못된 법령·항으로 연결되기 쉬운 API/원문 경계를 검사한다."""
import unittest

from delegation import parse, spans, fragments, fingerprint


class DelegationTests(unittest.TestCase):
    def test_xml_keeps_sibling_law_order(self):
        def item(no):
            return ("<위임법령조문정보><위임법령조문번호>" + no +
                    "</위임법령조문번호><링크텍스트>고용노동부령</링크텍스트>"
                    "<조항호목>제2조제2호</조항호목></위임법령조문정보>")
        xml = ("<lsDelegated><법령><법령정보><법령명>법</법령명>"
               "<법령일련번호>123</법령일련번호></법령정보><위임조문정보>"
               "<조정보><조문번호>2</조문번호></조정보><위임정보>"
               "<위임구분>시행규칙</위임구분><위임법령제목>규칙A</위임법령제목>" +
               item("3") + item("4") + "<위임구분>시행규칙</위임구분>"
               "<위임법령제목>규칙B</위임법령제목>" + item("5") +
               "</위임정보></위임조문정보></법령></lsDelegated>")
        mst, links = parse(xml)
        self.assertEqual(mst, "123")
        self.assertEqual([(x["법령"], x["대상"]) for x in links],
                         [("규칙A", "제3조"), ("규칙A", "제4조"), ("규칙B", "제5조")])

    def test_repeated_words_use_context_and_paragraph(self):
        text = "고용노동부령으로 정하는 대상과 고용노동부령으로 정하는 절차"
        link = {"위치": "제1조제2항", "문구": "고용노동부령", "문맥": "고용노동부령으로 정하는 절차"}
        self.assertEqual(spans(text, "제1조제2항", link), [(17, 23)])
        self.assertEqual(spans(text, "제1조제3항", link), [])
        self.assertEqual(spans("고용노동부령으로 정하는 교육", "제1조제2항", link), [])

    def test_middle_dots_and_spaces_keep_original_offsets(self):
        text = "요건은 대통령령으로  정하는 인력ㆍ시설"
        link = {"위치": "제1조", "문구": "대통령령", "문맥": "대통령령으로 정하는 인력·시설"}
        self.assertEqual(spans(text, "제1조", link), [(4, 8)])

    def test_branched_item_and_mok_are_scoped(self):
        text = "3의2. 각 목의 사항\n가. 대통령령으로 정한다\n나. 대통령령으로 정한다"
        a = {"조번호": "제1조", "항": [{"번호": "①", "호": [text]}]}
        part, loc, raw = next(fragments(a))
        self.assertEqual((part, loc), ("항0호0", "제1조제1항제3호의2"))
        link = {"위치": loc + "나목", "문구": "대통령령", "문맥": "대통령령으로 정한다"}
        self.assertEqual(spans(raw, loc, link), [(raw.rindex("대통령령"), raw.rindex("대통령령") + 4)])

    def test_fingerprint_detects_article_changes(self):
        doc = {"조문": [{"조번호": "제1조", "본문": "원문"}]}
        before = fingerprint(doc)
        doc["조문"][0]["위임"] = [{"대상": ["1:j:1"]}]
        self.assertEqual(before, fingerprint(doc))
        doc["조문"][0]["본문"] = "개정 원문"
        self.assertNotEqual(before, fingerprint(doc))


if __name__ == "__main__":
    unittest.main()
