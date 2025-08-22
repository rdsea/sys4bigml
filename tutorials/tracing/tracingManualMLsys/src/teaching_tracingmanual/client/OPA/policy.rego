package sys4bigml.violation

import data.sys4bigml.contract

# Define a rule to collect violation messages from multiple policies
violation_messages[msg] {
    violation_policy1[msg]
} # {
    # violation_policy2[msg]
#}

# Violation-detecting policy 1
violation_policy1[msg] {
    input.stage_id
    input.response_time
    input.response_time > contract.stages[input.stage_id].response_time_threshold
    msg := sprintf("Violation in stage %s: response time %.3f exceeds threshold %.1f", [input.stage_id, input.response_time, contract.stages[input.stage_id].response_time_threshold])
}

# Violation-detecting policy 2 (example)
# violation_policy2[msg] {
    # input.stage_id
    # input.error_rate
    # input.error_rate > contract.stages[input.stage_id].error_rate_threshold
    # msg := sprintf("Violation in stage %s: error rate %d exceeds threshold %d", [input.stage_id, input.error_rate, contract.stages[input.stage_id].error_rate_threshold])
# }

# Set violation to true if any of the violation policies are triggered
violation = true {
    count(violation_messages) > 0
}

# Define a rule to return the violation status and messages
get_violation_result[result] {
    violation
    msgs := {msg | violation_messages[msg]}
    result := {
        "violation": violation,
        "messages": [msg | msg := msgs[_]]
    }
}