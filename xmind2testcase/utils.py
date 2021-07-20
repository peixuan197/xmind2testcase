#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import json
import os
import xmind
import logging
from xmind2testcase.parser import xmind_to_testsuites
import xlwt
import xlrd
from tkinter import *

def get_absolute_path(path):
    """
        Return the absolute path of a file

        If path contains a start point (eg Unix '/') then use the specified start point
        instead of the current working directory. The starting point of the file path is
        allowed to begin with a tilde "~", which will be replaced with the user's home directory.
    """
    fp, fn = os.path.split(path)
    if not fp:
        fp = os.getcwd()
    fp = os.path.abspath(os.path.expanduser(fp))
    return os.path.join(fp, fn)


def get_xmind_testsuites(xmind_file):
    """Load the XMind file and parse to `xmind2testcase.metadata.TestSuite` list"""
    xmind_file = get_absolute_path(xmind_file)
    workbook = xmind.load(xmind_file)
    xmind_content_dict = workbook.getData()
    logging.debug("loading XMind file(%s) dict data: %s", xmind_file, xmind_content_dict)

    if xmind_content_dict:
        testsuites = xmind_to_testsuites(xmind_content_dict)
        return testsuites
    else:
        logging.error('Invalid XMind file(%s): it is empty!', xmind_file)
        return []


def get_xmind_testsuite_list(xmind_file):
    """Load the XMind file and get all testsuite in it

    :param xmind_file: the target XMind file
    :return: a list of testsuite data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuite data list...', xmind_file)
    testsuite_list = get_xmind_testsuites(xmind_file)
    suite_data_list = []

    for testsuite in testsuite_list:
        product_statistics = {'case_num': 0, 'non_execution': 0, 'pass': 0, 'failed': 0, 'blocked': 0, 'skipped': 0}
        for sub_suite in testsuite.sub_suites:
            suite_statistics = {'case_num': len(sub_suite.testcase_list), 'non_execution': 0, 'pass': 0, 'failed': 0, 'blocked': 0, 'skipped': 0}
            for case in sub_suite.testcase_list:
                if case.result == 0:
                    suite_statistics['non_execution'] += 1
                elif case.result == 1:
                    suite_statistics['pass'] += 1
                elif case.result == 2:
                    suite_statistics['failed'] += 1
                elif case.result == 3:
                    suite_statistics['blocked'] += 1
                elif case.result == 4:
                    suite_statistics['skipped'] += 1
                else:
                    logging.warning('This testcase result is abnormal: %s, please check it: %s', case.result, case.to_dict())
            sub_suite.statistics = suite_statistics
            for item in product_statistics:
                product_statistics[item] += suite_statistics[item]

        testsuite.statistics = product_statistics
        suite_data = testsuite.to_dict()
        suite_data_list.append(suite_data)

    logging.info('Convert XMind file(%s) to testsuite data list successfully!', xmind_file)
    return suite_data_list


def get_xmind_testcase_list(xmind_file):
    """Load the XMind file and get all testcase in it

    :param xmind_file: the target XMind file
    :return: a list of testcase data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases dict data...', xmind_file)
    testsuites = get_xmind_testsuites(xmind_file)
    testcases = []

    for testsuite in testsuites:
        product = testsuite.name
        for suite in testsuite.sub_suites:
            for case in suite.testcase_list:
                case_data = case.to_dict()
                case_data['product'] = product
                case_data['suite'] = suite.name
                testcases.append(case_data)

    logging.info('Convert XMind file(%s) to testcases dict data successfully!', xmind_file)
    return testcases


def xmind_testsuite_to_json_file(xmind_file):
    """Convert XMind file to a testsuite json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuites json file...', xmind_file)
    testsuites = get_xmind_testsuite_list(xmind_file)
    testsuite_json_file = xmind_file[:-6] + '_testsuite.json'

    if os.path.exists(testsuite_json_file):
        os.remove(testsuite_json_file)
        # logging.info('The testsuite json file already exists, return it directly: %s', testsuite_json_file)
        # return testsuite_json_file

    with open(testsuite_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testsuites, indent=4, separators=(',', ': '), ensure_ascii=False))
        logging.info('Convert XMind file(%s) to a testsuite json file(%s) successfully!', xmind_file, testsuite_json_file)

    return testsuite_json_file


def xmind_testcase_to_json_file(xmind_file):
    """Convert XMind file to a testcase json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases json file...', xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)
    testcase_json_file = xmind_file[:-6] + '.json'

    if os.path.exists(testcase_json_file):
        os.remove(testcase_json_file)
        # logging.info('The testcase json file already exists, return it directly: %s', testcase_json_file)
        # return testcase_json_file

    with open(testcase_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testcases, indent=4, separators=(',', ': '), ensure_ascii=False))
        logging.info('Convert XMind file(%s) to a testcase json file(%s) successfully!', xmind_file, testcase_json_file)

    return testcase_json_file


def export_to_excel(xmind_file):
    """
    :param xmind_file: xmind文件
    :return: 返回excel文件
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuites json file...', xmind_file)
    testsuites = get_xmind_testsuite_list(xmind_file)
    first_row = ['模块','前置条件','用例名称','优先级','执行步骤','预期结果','备注']

    # 设置各种样式
    alignment = xlwt.Alignment()
    alignment.vert = xlwt.Alignment.VERT_CENTER

    style = xlwt.XFStyle()
    style.alignment = alignment

    font_first_row = xlwt.Font()
    # font_first_row.bold = True
    font_first_row.height = 300
    font_first_pattert = xlwt.Pattern()
    font_first_pattert.pattern = xlwt.Pattern.SOLID_PATTERN
    font_first_pattert.pattern_fore_colour = 21


    style_first_row = xlwt.XFStyle()
    style_first_row.font = font_first_row
    style_first_row.pattern = font_first_pattert


    if testsuites:
        story = testsuites[0]
        file_name = story['name']
        if os.path.exists(file_name + '.xls'):
            os.remove(file_name + '.xls')
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet(file_name)
        for item in first_row:
            worksheet.write(0,first_row.index(item),item,style_first_row)
            worksheet.col(first_row.index(item)).width =5000
        row = 1
        modle_index = 1
        case_index = 1
        step_count = 0
        modle_count = 0
        # 记录每列的最大宽度
        col_width = []

        for model in story['sub_suites']:
            if len(model['testcase_list']) > 0:
                for case in (model['testcase_list']):
                    if len(case['steps']) > 0:
                        step_count = len(case['steps'])
                        for index, step in enumerate(case['steps']):

                            worksheet.write(row, 4, str(index + 1) + '、' + step['actions'])
                            if len(step['expectedresults']) > 0:
                                worksheet.write(row, 5, str(index + 1) + '、' + step['expectedresults'])
                            worksheet.write(row, 6, step['remark'])

                            row += 1
                        # 合并同一个用例的相同部分

                        worksheet.write_merge(case_index, case_index + step_count - 1, 1, 1, case['preconditions'],style)
                        worksheet.write_merge(case_index, case_index + step_count - 1, 2, 2, case['name'],style)
                        worksheet.write_merge(case_index, case_index + step_count - 1, 3, 3, case['importance'],style)
                        case_index += step_count
                        modle_count += step_count

                    else:
                        # worksheet.write(row, 0, model['name'])
                        # step_count += 1
                        worksheet.write(row, 1, case['preconditions'])
                        worksheet.write(row, 2, case['name'])
                        worksheet.write(row, 3, case['importance'])
                        worksheet.write(row, 6, case['remark'])

                        row = row + 1
                        case_index += 1
                        modle_count += 1
                worksheet.write_merge(modle_index, modle_index + modle_count - 1, 0, 0, model['name'],style)
                modle_index += modle_count
                modle_count = 0
            else:
                worksheet.write(row, 0, model['name'])
                row += 1
                case_index += 1

        workbook.save(os.path.join(os.path.dirname(xmind_file),file_name + '.xls'))

        return os.path.join(os.path.dirname(xmind_file),file_name + '.xls')


if __name__ == '__main__':
    xmind_file = '../docs/test.xmind'
    export_to_excel(xmind_file)

