from datetime import datetime, timedelta

from pytest_mock.plugin import MockerFixture


class FakeModelSelect(list):
    def dicts(self):
        lst = [
            {"content": per_msg["content"], "hour": per_msg["hour"]} for per_msg in self
        ]
        return lst


def patch_get_labeled_message_content_by_time(mocker: MockerFixture):
    import json
    from src.plugins.group_yashima.report.database.operator import DBOperator

    fake_msgs = FakeModelSelect(
        [
            {"content": json.dumps([{"type": "text"}]), "hour": "00"},
            {"content": json.dumps([{"messages": []}]), "hour": "00"},
            {"content": json.dumps([{"type": "image"}]), "hour": "00"},
            {"content": json.dumps([{"type": "image"}]), "hour": "05"},
            {"content": json.dumps([{"type": "text"}]), "hour": "08"},
        ]
    )
    mocker.patch.object(
        DBOperator, "get_labeled_message_content_by_time", return_value=fake_msgs
    )


def patch_get_group_message_between(mocker: MockerFixture):
    import json
    from src.plugins.group_yashima.report.database.operator import DBOperator

    fake_msgs = FakeModelSelect(
        [
            {"content": json.dumps([{"type": "text"}]), "hour": "00"},
            {"content": json.dumps([{"messages": []}]), "hour": "00"},
            {"content": json.dumps([{"type": "image"}]), "hour": "00"},
        ]
    )
    mocker.patch.object(DBOperator, "get_group_message_between", return_value=fake_msgs)


class TestAnalyzer:
    def test_get_message_type_counts_between(self, mocker: MockerFixture):
        from src.plugins.group_yashima.report.builder.analyzer import ReportAnalyzer

        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = datetime.now().replace(hour=23, minute=23, second=59)

        patch_get_group_message_between(mocker)
        counters = ReportAnalyzer().get_message_type_counts_between(
            today_start, today_end
        )

        assert len(counters) == 1
        assert counters[0] is not None

        test_counters = [{"text": 2, "image": 1}]
        actual_counters = [{"text": counters[0]["text"], "image": counters[0]["image"]}]

        assert test_counters == actual_counters

    def test_get_message_type_counts_between_with_group(self, mocker: MockerFixture):
        from src.plugins.group_yashima.report.builder.analyzer import ReportAnalyzer

        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = datetime.now().replace(hour=23, minute=23, second=59)

        patch_get_labeled_message_content_by_time(mocker)
        counters = ReportAnalyzer().get_message_type_counts_between(
            today_start, today_end, group_by=timedelta(hours=1)
        )

        assert len(counters) == 24

        test_counters = [
            {"text": 2, "image": 1},
            {"text": 0, "image": 1},
            {"text": 1, "image": 0},
        ]
        actual_counters = []
        for per_counter in counters:
            if not per_counter:
                continue
            actual_counters.append(
                {"text": per_counter["text"], "image": per_counter["image"]}
            )

        assert test_counters == actual_counters
