#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import logging
from xmind2testcase.metadata import TestSuite, TestCase, TestStep

config = {'sep': ' ',
          'valid_sep': '&>+/-',
          'precondition_sep': '\n----\n',
          'summary_sep': '\n----\n',
          'ignore_char': '#!！'
          }


def xmind_to_testsuites(xmind_content_dict):
    """convert xmind file to `xmind2testcase.metadata.TestSuite` list"""
    suites = []

    for sheet in xmind_content_dict:
        logging.debug('start to parse a sheet: %s', sheet['title'])
        root_topic = sheet['topic']
        sub_topics = root_topic.get('topics', [])

        if sub_topics:
            root_topic['topics'] = filter_empty_or_ignore_topic(sub_topics)
        else:
            logging.warning('This is a blank sheet(%s), should have at least 1 sub topic(test suite)', sheet['title'])
            continue
        suite = sheet_to_suite(root_topic)
        # suite.sheet_name = sheet['title']  # root testsuite has a sheet_name attribute
        logging.debug('sheet(%s) parsing complete: %s', sheet['title'], suite.to_dict())
        suites.append(suite)

    return suites


def filter_empty_or_ignore_topic(topics):
    """filter blank or start with config.ignore_char topic"""
    result = [topic for topic in topics if not(
            topic['title'] is None or
            topic['title'].strip() == '' or
            topic['title'][0] in config['ignore_char'])]

    for topic in result:
        sub_topics = topic.get('topics', [])
        topic['topics'] = filter_empty_or_ignore_topic(sub_topics)

    return result


def filter_empty_or_ignore_element(values):
    """Filter all empty or ignore XMind elements, especially notes、comments、labels element"""
    result = []
    for value in values:
        if isinstance(value, str) and not value.strip() == '' and not value[0] in config['ignore_char']:
            result.append(value.strip())
    return result


def sheet_to_suite(root_topic):
    """convert a xmind sheet to a `TestSuite` instance"""
    suite = TestSuite()
    root_title = root_topic['title']
    separator = root_title[-1]

    if separator in config['valid_sep']:
        logging.debug('find a valid separator for connecting testcase title: %s', separator)
        config['sep'] = separator  # set the separator for the testcase's title
        root_title = root_title[:-1]
    else:
        config['sep'] = ' '

    suite.name = root_title
    suite.details = root_topic['note']
    suite.sub_suites = []

    for suite_dict in root_topic['topics']:
        suite.sub_suites.append(parse_testsuite(suite_dict))

    return suite


def parse_testsuite(suite_dict):
    testsuite = TestSuite()
    testsuite.name = suite_dict['title']
    # xmind无法获取note字段
    testsuite.details = suite_dict['note']
    testsuite.testcase_list = []
    logging.debug('start to parse a testsuite: %s', testsuite.name)

    for cases_dict in suite_dict.get('topics', []):
        case_name = ""
        temp = TestCase()
        new_case = TestCase()
        first = 1
        index = 0
        cases_iter = list(recurse_parse_testcase(cases_dict))
        merge_flag = 0
        for case in cases_iter:
            index += 1
            next_case = transform_case(case)
            case_name = next_case.name
            if case_name == temp.name:
                # 说明2者是同一条用例，则合并
                new_case = merge_case(temp,next_case)
                merge_flag = 1
                if index == len(cases_iter):
                    # 最后一条用例，直接加入用例列表中
                    testsuite.testcase_list.append(new_case)

                temp = new_case
            else:
                if first == 1:
                    if index == len(cases_iter):
                        # 只有1条用例
                        testsuite.testcase_list.append(next_case)
                        continue
                    else:
                        # 首个用例不加入列表中
                        first = 0
                        temp = next_case
                        continue
                # 如果用例没有合并过，直接添加temp用例
                if merge_flag == 1:
                    testsuite.testcase_list.append(new_case)
                    merge_flag = 0
                else:
                    testsuite.testcase_list.append(temp)
                if index == len(cases_iter):
                    # 最后一条用例，直接加入用例列表中
                    testsuite.testcase_list.append(next_case)
                temp = next_case
            # if index == len()

    logging.debug('testsuite(%s) parsing complete: %s', testsuite.name, testsuite.to_dict())
    return testsuite


def merge_case(case1,case2):
    """
    合并2条相同的用例
    """
    new_case = TestCase()
    new_case.name = case1.name
    new_case.importance = case1.importance
    new_case.preconditions = case1.preconditions
    new_case.steps = case1.steps + case2.steps

    return new_case


def transform_case(case_old):
    """
    将解析出来的用例转换成我们需要的格式
    """
    case_new = TestCase()
    if case_old:
        if len(case_old.preconditions) == 0:
            # 如果用例没有前置条件，说明他不符合模板规则，则把当前name作为name
            case_new.name = case_old.name
        else:
            case_new.name = case_old.preconditions[-1]
            case_new.preconditions = ' > '.join(case_old.preconditions[:-1])
        case_new.importance = case_old.importance
        case_new.steps = []

        if case_old.steps and len(case_old.steps) > 0:
            for step in case_old.steps:
                tem_step = TestStep()
                tem_step.actions = case_old.name
                tem_step.expectedresults = tem_step.expectedresults + '\n' + step.actions + step.expectedresults
                tem_step.remark = step.remark
                tem_step.priority = case_old.importance

                case_new.steps.append(tem_step)

        else:
            tem_step = TestStep()
            tem_step.actions = case_old.name
            tem_step.remark = case_old.remark
            tem_step.priority = case_old.importance
            case_new.steps.append(tem_step)
        # case_new.remark = case_old.remark

    return case_new


def recurse_parse_testcase(case_dict, parent=None):

    if is_testcase_topic(case_dict):
        case = parse_a_testcase(case_dict, parent)
        yield case
    else:
        if not parent:
            parent = []

        parent.append(case_dict)

        for child_dict in case_dict.get('topics', []):
            for case in recurse_parse_testcase(child_dict, parent):
                yield case

        parent.pop()


def is_testcase_topic(case_dict):
    """A topic with a priority marker, or no subtopic, indicates that it is a testcase"""
    # priority = get_priority(case_dict)
    # if priority:
    #     return True
    priority = get_priority_for_tapd(case_dict)
    if priority != -1:
        return True

    children = case_dict.get('topics', [])
    if children:
        return False

    return True


def parse_a_testcase(case_dict, parent):
    testcase = TestCase()
    testcase.importance = get_priority_for_tapd(case_dict)
    if testcase.importance == -1:
        testcase.importance = 1
    if '|' in case_dict['title']:
        case_dict['title'] = case_dict['title'].split('|')[-1]

    topics = parent + [case_dict] if parent else [case_dict]

    testcase.name = gen_testcase_title(topics)
    if testcase.name:

        preconditions = testcase.name.split(" ")[:-1]
        testcase.name = testcase.name.split(" ")[-1]

        testcase.preconditions = preconditions if preconditions else []

    summary = gen_testcase_summary(topics)
    testcase.summary = summary if summary else testcase.name
    testcase.execution_type = get_execution_type(topics)
    step_dict_list = case_dict.get('topics', [])
    if step_dict_list:
        fist_step = step_dict_list[0]
        if 'R|' in fist_step['title']:
            testcase.remark = fist_step['title'].split('|')[-1]
        else:
            testcase.steps = parse_test_steps(step_dict_list)

    # the result of the testcase take precedence over the result of the teststep
    testcase.result = get_test_result(case_dict['markers'])

    if testcase.result == 0 and testcase.steps:
        for step in testcase.steps:
            if step.result == 2:
                testcase.result = 2
                break
            if step.result == 3:
                testcase.result = 3
                break

            testcase.result = step.result  # there is no need to judge where test step are ignored

    logging.debug('finds a testcase: %s', testcase.to_dict())

    return testcase


def get_execution_type(topics):
    labels = [topic.get('label', '') for topic in topics]
    labels = filter_empty_or_ignore_element(labels)
    exe_type = 1
    for item in labels[::-1]:
        if item.lower() in ['自动', 'auto', 'automate', 'automation']:
            exe_type = 2
            break
        if item.lower() in ['手动', '手工', 'manual']:
            exe_type = 1
            break
    return exe_type


def get_priority(case_dict):
    """Get the topic's priority（equivalent to the importance of the testcase)"""
    # if isinstance(case_dict['markers'], list):
    #     for marker in case_dict['markers']:
    #         if marker.startswith('priority'):
    #             return int(marker[-1])
    if "|" not in case_dict['title']:
        return None
    else:
        if 'p0' in case_dict['title'].lower():
            return 0
        if 'p1' in case_dict['title'].lower():
            return 1
        if 'p2' in case_dict['title'].lower():
            return 2

    return 1


def get_priority_for_tapd(case_dict):
    """
    tapd-xmind 无法获取图标信息，只能以字段P0，P1，P2标注用例
    """
    if 'p0' in case_dict['title'].lower():
        return 0
    elif 'p1' in case_dict['title'].lower():
        return 1
    elif 'p2' in case_dict['title'].lower():
        return 2
    else:
        return -1

    return 1


def gen_testcase_title(topics):
    """Link all topic's title as testcase title"""
    titles = [topic['title'] for topic in topics]
    titles = filter_empty_or_ignore_element(titles)

    # when separator is not blank, will add space around separator, e.g. '/' will be changed to ' / '
    separator = config['sep']
    if separator != ' ':
        separator = ' {} '.format(separator)

    return separator.join(titles)


def gen_testcase_preconditions(topics):
    notes = [topic['note'] for topic in topics]
    notes = filter_empty_or_ignore_element(notes)
    return config['precondition_sep'].join(notes)


def gen_testcase_summary(topics):
    comments = [topic['comment'] for topic in topics]
    comments = filter_empty_or_ignore_element(comments)
    return config['summary_sep'].join(comments)


def parse_test_steps(step_dict_list):
    steps = []

    for step_num, step_dict in enumerate(step_dict_list, 1):
        test_step = parse_a_test_step(step_dict)
        test_step.step_number = step_num
        steps.append(test_step)

    return steps


def parse_a_test_step(step_dict):
    test_step = TestStep()
    test_step.actions = step_dict['title']

    expected_topics = step_dict.get('topics', [])


    if expected_topics:  # have expected result
        # 只有一条期望的时候
        if len(expected_topics) == 1:
            expected_topic = expected_topics[0]
            # 需要判断后面的节点是预期结果还是备注信息
            if 'R|' in expected_topic['title']:
                test_step.remark = expected_topic['title'].split('|')[-1]
            else:
                test_step.expectedresults = expected_topic['title']  # one test step action, one test expected result
                markers = expected_topic['markers']
                test_step.result = get_test_result(markers)
                remark = expected_topic.get('topics', [])
                if remark:
                    re = remark[0]
                    test_step.remark = re['title'].split('|')[-1]
        else:
            # 如果有多条期望，合并展示
            for exp in expected_topics:
                if 'R|' in exp['title']:
                    test_step.remark = test_step.remark + '\n' + exp['title'].split('|')[-1]
                else:
                    test_step.expectedresults = test_step.expectedresults + '\n' + exp['title']
    else:  # only have test step
        markers = step_dict['markers']
        test_step.result = get_test_result(markers)

    logging.debug('finds a teststep: %s', test_step.to_dict())
    return test_step


def get_test_result(markers):
    """test result: non-execution:0, pass:1, failed:2, blocked:3, skipped:4"""
    if isinstance(markers, list):
        if 'symbol-right' in markers or 'c_simbol-right' in markers:
            result = 1
        elif 'symbol-wrong' in markers or 'c_simbol-wrong' in markers:
            result = 2
        elif 'symbol-pause' in markers or 'c_simbol-pause' in markers:
            result = 3
        elif 'symbol-minus' in markers or 'c_simbol-minus' in markers:
            result = 4
        else:
            result = 0
    else:
        result = 0

    return result








