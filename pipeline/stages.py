"""The seven workflow stages. Each one is a thin wrapper around a prompt template."""
from .llm import load_json, run_stage


def intake(mode, brief):
    return run_stage("intake", mode, brief=brief)


def clarify(mode, intake_result):
    return run_stage("clarify", mode, intake=intake_result)


def options(mode, intake_result, answers):
    patterns = load_json("knowledge/cloud_patterns.json")
    return run_stage("options", mode, intake=intake_result, answers=answers, patterns=patterns)


def tradeoff(mode, option_list):
    return run_stage("tradeoff", mode, options=option_list)


def recommend(mode, option_list, matrix):
    return run_stage("recommend", mode, options=option_list, matrix=matrix)


def adr(mode, intake_result, option_list, recommendation, selected_id):
    return run_stage(
        "adr", mode, intake=intake_result, options=option_list,
        recommendation=recommendation, selected_id=selected_id,
    )


def diagram(mode, option_list, selected_id):
    return run_stage("diagram", mode, options=option_list, selected_id=selected_id)


def summary(mode, recommendation, selected_id):
    return run_stage("summary", mode, recommendation=recommendation, selected_id=selected_id)
