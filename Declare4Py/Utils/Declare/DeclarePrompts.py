
class DeclarePrompts(str):
    # General aim and basic templates
    INSTRUCTIONS_AND_TEMPLATES = """Process discovery is a type of process mining aiming to represent the process model explaining how the process is executed. Our focus is on the discovery of an imperative process model. Recently, we developed a framework that allows for some declarative constraints as input to discover better imperative models. Declarative models are close to the natural language, however for a domain expert, they might not be familiar. Therefore, we need your help to translate the process description given as a text to the declarative constraints we need for the discovery of imperative process models.
Consider only the following declarative constraint definitions where a, b, c, and d are activities and template example-template(x,y) specifies a template named "example-template" and x and y can be on of the activities from the set of all activities. Do not reason based on the template names and only use explanations to understand the meaning of specific templates:

- at-most(A): A occurs at most once. 
	1.	Some examples satisfying this constraint:
		- The process starts with activity B for setup, followed by A for approval, then C for data collection, and ends with D for implementation. Optional execution of B can occur again before C.
		- The workflow begins with C for initial data collection, followed by D for setup, then A for mandatory approval, and concludes with B for detailed planning.
		- The process initiates with D for setup, followed by B for planning, C for data analysis, and finally A for essential approval. Optional execution of C may occur again after B. 
	2.	Some examples violating this constraint:
		- The process starts with A for initial approval, followed by B for planning, then loops back to A for re-approval, and ends with C for data analysis and D for implementation.
		- Begin with C for data collection, followed by A for approval, then B for planning, another A for re-approval, and ends with D for execution.
		- The workflow involves D for setup, followed by parallel execution of A for initial approval and B for planning, then A second occurrence of A for final approval, and C for final data analysis.

- existence(A): A occurs at least once, which means the existence of activity A is mandatory.
	1. Some examples satisfying this constraint:
		- The process starts with activity B for initial setup, followed by A for mandatory approval, then C for data collection, and finally D for implementation. Optional execution of C can occur again before d.
		- The workflow begins with D for setup, followed by A for critical approval, then parallel execution of B for planning and C for analysis, and concludes with D for finalization.
		- Activity C starts with data gathering, then loops to B for planning, followed by A for essential approval, and ends with D for implementation.
		- all the customers start the process with activity A.
	2. Some examples violating this constraint:
		- The process starts with B for initial tasks, followed by C for data analysis, and concludes with D for implementation. Optional execution of C can occur again before D.
		- Begin with D for setup, followed by B for detailed planning, then C for further analysis, and ends with D for final execution. 
		- The workflow involves C for initial data collection, followed by parallel execution of B for planning and D for implementation, and ends with another round of C.
		- Either one of the activities A or B occurs. Each trace can only have A or B.

- response(A,B): If A occurs, then B occurs after A.
	1. Some examples satisfying this constraint:
		- The process starts with C for data collection, then A for approval, followed by B for planning, and finally D for implementation. Optional execution of C may occur again before D.
		- Activity D begins with preliminary tasks, then A for approval, followed by parallel execution of B for planning and C for analysis, ending with D for finalization.
		- The workflow initiates with A for approval, loops back to A second approval if needed, then proceeds to B for detailed planning, and concludes with C for execution.
		- All the occurrences of activity A should be followed by activity B.
	2. Some examples violating this constraint:
		- The process starts with B for initial setup, followed by C for data analysis, then A for approval, and ends with D for implementation.
		- Begin with C for data gathering, followed by A for approval, then D for execution, and optionally B for post-implementation review.
		- The process involves D for setup, followed by A for approval, and then C for analysis. An optional activity B for final planning may or may not occur.

- precedence(A,B): B occurs only if preceded by A.
	1. Some examples satisfying this constraint:
		- The process begins with activity A for approval, followed by C for data collection, and then B for planning. Optional execution of D can occur anytime before or after B.
		- Activity D initiates the setup, then A for mandatory approval, followed by parallel execution of C for analysis and B for planning, and concludes with D for finalization.
		- The workflow starts with C for initial tasks, followed by A for approval, then B for detailed planning, and ends with A loop back to C for further analysis if needed.
		- After execution of activity A, some cases will continue with activity B and some cases will continue with activity C.
	2. Some examples violating this constraint:
		- The process starts with C for data gathering, followed by B for planning, then A for approval, and ends with D for implementation.
		- Begin with D for initial setup, followed by parallel execution of B for planning and C for analysis, and finally A for approval.
		- The workflow involves D for setup, followed by C for data collection, B for planning, and ends with an optional activity A for final approval.

- co-existence(A,B): A and B occur together. 
	1. Some examples satisfying this constraint:
		- The process starts with B for initial setup, followed by A for approval, then C for data collection, and ends with D for implementation. Optional execution of B can occur again before C.
		- Activity A begins with approval, followed by parallel execution of B for planning and C for data analysis, and concludes with D for finalization.
		- The workflow starts with D for setup, followed by A for approval, B for planning, and ends with C for execution. Optional execution of C may occur again after B.
	2. Some examples violating this constraint:
		- The process begins with C for data collection, followed by D for setup, then B for planning, and ends with another round of C.
		- Start with D for setup, followed by C for data analysis, then A for approval, and ends with C for final review.
		- The workflow involves C for initial data gathering, followed by parallel execution of D for setup and B for planning, and concludes with C for finalization.

- not-co-existence(A,B): A and B never occur together.
	1. Some examples satisfying this constraint:
		- The process starts with A for approval, followed by C for data collection, then D for implementation. Optional execution of C can occur again before D.
		- Begin with B for initial setup, followed by C for analysis, then D for execution. An optional activity C can repeat after D.
		- The workflow starts with C for data gathering, then moves to D for setup, followed by optional repetitions of C.
		- In our process activities A and B cannot occur together.
		- Some cases have activity A and the other cases have activity B.
		- If activity A does not occur, then activity B will occur.
	2. Some examples violating this constraint:
		- The process begins with A for approval, followed by B for planning, then C for data collection, and ends with D for implementation.
		- Start with C for data analysis, then A for approval, followed by D for execution, and ends with B for final review.
		- The workflow involves D for setup, followed by parallel execution of A for approval and B for planning, and concludes with C for finalization.

- not-succession(A,B): B cannot occur after A.
	1. Some examples satisfying this constraint:
		- The process starts with A for approval, followed by C for data collection, and ends with D for implementation. Optional execution of C can occur again before D.
		- Begin with B for initial setup, followed by D for setup, then A for approval, and finally C for analysis.
		- The workflow starts with C for data gathering, followed by A for approval, then D for execution, and optional repetitions of C.
	2. Some examples violating this constraint:
		- The process begins with A for approval, followed by B for planning, then C for data collection, and ends with D for implementation.
		- Start with C for data analysis, then A for approval, followed by D for execution, and ends with B for final review.
		- The workflow involves D for setup, followed by parallel execution of A for approval and C for analysis, then B for planning, and concludes with C for finalization.

- responded-existence(A,B): If A occurs in the trace, then B occurs as well.
	1. Some examples satisfying this constraint:
		- The process starts with B for initial setup, followed by A for approval, then C for datA collection, and ends with D for implementation. Optional execution of B can occur again before c.
		- Begin with A for initial approval, followed by D for setup, then B for planning, and finally C for analysis.
		- The workflow starts with C for data gathering, followed by A for approval, then D for execution, and optional repetitions of B for planning.
	2. Some examples violating this constraint:
		- The process begins with A for approval, followed by C for data collection, then D for implementation. Optional execution of C can occur again before d.
		- Start with C for data analysis, followed by A for approval, then D for execution, and ends with C for final review.
		- The workflow involves D for setup, followed by A for approval, then parallel execution of C for analysis and B for planning, and concludes with C for finalization.

Some more instructions:
- It is not possible to generate constraints like response(a, (b or c)). The first and second elements must be a single activity

For each task, I provide the set of activity labels that exist in the process with a short description. Then, I present a text written by a process expert and want you to translate it to declarative constraints and write it in a plaintext block.
"""

    # Additional templates
    ADDITIONAL_TEMPLATES = """In addition to the constraint models provided above, there are others:

- succession(A,B): If A occurs, then B must also occur (at some point later), and vice versa: if B occurs, then A must have occurred before. A and B are connected; one implies the other, in order.
	1. Some examples satisfying this constraint:
		- If a customer places an order (A), then an invoice must be issued (B) and if an invoice is issued, the order must have been placed
		- The process begins with (A) requesting creation, followed by (B) requesting approval, then proceeding to C and D for execution.
		- Workflow starts with C, followed by A for initial check, then d, and finally B for final approval.
	2. Some examples violating this constraint:
		- The process starts with A, then goes to C and D, but B is never executed.
		- B occurs early in the process, followed by C, but A never takes place beforehand.
		- The workflow has A at the beginning, C in the middle, and ends with D - B is completely missing.
- choice(A,B): A or B have to occur at least once.
	1. Some examples satisfying this constraint:
		- The process begins with A for document review, followed by C, and ends with D. B never occurs.
		- The workflow includes B for data approval after C, but A is not present.
		- The trace includes both A and B, with A occurring before C, and B happening after D.
	2. Some examples violating this constraint:
		- The trace includes only C, D, and E - neither A nor B are present.
		- Workflow starts with C, then moves to D, and ends with E. No trace of A or B.
		- The entire process involves only repeated executions of C and D, excluding both A and B.

- exclusive-choice(A,B): A or B have to occur at least once but not both.
	1. Some examples satisfying this constraint:
		- The process starts with A for submission, continues with C, and ends with D - B never appears.
		- Only B for manual override occurs midway through the trace; A is never executed.
		- The process starts with C then reaches a step where a condition is either verified of not, based on the condition result the process proceeds with A or B, only one is chosen
	2. Some examples violating this constraint:
		- The process includes A for creation, followed by B for confirmation later in the trace.
		- After C, both A and B are executed as part of A dual-check process.
		- The workflow loops through both A and B multiple times before finalizing with D.

- not-exclusive-choice(A,B): It is not allowed that only one of A or B occurs; if one happens, the other must also occur. Both A and B must either happen together or not at all.
	1. Some examples satisfying this constraint:
		- If A contract is signed (A), then onboarding (B) must also occur, and vice versa.
		- The process includes A for creation, followed by B for confirmation later in the trace.
		- After C, both A and B are executed as part of a dual-check process.
		- The workflow loops through both A and B multiple times before finalizing with D.
	2. Some examples violating this constraint:
		- Only A is executed in the trace, without A corresponding B.
		- The workflow contains B for approval but skips A entirely.
		- A appears early in the process, but B never occurs, violating the required pairing.

- not-chain-succession(A,B): It is forbidden that B directly follows A (i.e., with no events in between). B can happen after A, but not immediately after.
	1. Some examples satisfying this constraint:
		- A system check (B) must not follow a reboot (A) immediately.
		- The process starts with A, followed by C, and only then B for validation.
		- A initiates the workflow, followed by D, E, and then B appears toward the end.
		- B appears early, then A occurs, and later C finishes the trace. At no point does B directly follow A.
	2. Some examples violating this constraint:
		- The trace begins with A, and B occurs immediately after as the second event.
		- A is executed, followed directly by B, with no intermediary steps.
		- A mid-process A is followed instantly by B without interruption

- chain-succession(A,B): A and B occur in the process instance if and only if the latter immediately follows the former.
	1. Some examples satisfying this constraint:
		- After scanning a product (A), the system must immediately log the scan result (B).
		- The trace is A → B → C → D. Every A is immediately followed by B, and every B has A just before it.
		- The process includes C, then A → B, and then D. 
		- A single A → B pair appears, with no other instances of A or B elsewhere in the trace.
		- A sequence like C → A → B → A → B → C is allowed by this constraint
	2. Some examples violating this constraint:
		- A is followed by C, with B appearing later - B does not directly follow A.
		- B appears without A preceding A.
		- One A is followed by B, but another B shows up without any prior A.
		- Sequences like B → C → A → A → C and B → C → A → A → B → C are not allowed

- chain-response(A,B): Each time A occurs in the process instance, then B occurs immediately afterwards, with no other action in between.
	1. Some examples satisfying this constraint:
		- A → B → C → D: every A is directly followed by B.
		- C → B → D: B can occur even without A prior.
		- The trace has one A → B sequence; any B not preceded by A is still allowed.
	2. Some examples violating this constraint:
		- A → C → B: B does not immediately follow A.
		- A appears but is followed by D, not B.
		- Multiple A events occur, but none are immediately followed by B.

- chain-precedence(A,B): Each time B occurs in the process instance, then A occurs immediately beforehand.
	1. Some examples satisfying this constraint:
		- A → B → C → D: B occurs immediately after A and nowhere else.
		- C → A → B → D: B is always and only right after A.
		- A → C → D: A can occur even without B
	2. Some examples violating this constraint:
		- B occurs first without any A before it.
		- A → C → B: B is not immediately after A.
		- B appears multiple times, but not every instance is preceded by A directly

- responded-existence (A,B): If A occurs, B must occur as well.
	1. Some examples satisfying this constraint:
		- A occurs early, and B appears at the end.
		- C → A → D → B: both are in the trace, regardless of position.
		- The trace has multiple As and Bs interspersed - every A is matched by at least one B somewhere.
	2. Some examples violating this constraint:
		- A occurs, but B is entirely absent from the trace.
		- Multiple As appear with no Bs at all.
		- A is in the trace, followed only by C, D, and E - no B.

- alternate-response(A,B): If A occurs, then B must eventually follow without any other A in between.
	1. Some examples satisfying this constraint:
		- A → B → A → B → C: every A is followed by B before another A occurs.
		- C → A → B → D: only one A, and it’s followed by B.
		- A → B → C → D: A single instance of A followed by B, with no second A.
	2. Some examples violating this constraint:
		- A → A → B: second A occurs before B appears.
		- A → C → A → B: B doesn’t follow the first A before the second A.
		- A → D → A → C → B: multiple As without Bs in between.

- alternate-precedence(A,B): B can occur only if A has occurred before, without any other B in between.
	1. Some examples satisfying this constraint:
		- The employee submits the report (A) before the manager approves it (B), and then the document is finalized.
		- The analyst submits one report (A) and gets it approved (B), then submits another (A) which is also approved (B).
	2. Some examples violating this constraint:
		- The manager approves the report (B) even though it was never submitted (A) beforehand.
		- The employee submits a report (A), gets it approved (B), and then a second approval (B) happens without a new submission (A).
		- The system logs an approval (B) first, then a submission (A) - violating the required order.

- alternate-succession(A,B): Between any two A events, there must be exactly one B. So, B must occur after each A, but no two As without a B in between. A and B alternate.
	1. Some examples satisfying this constraint:
		- Each request (A) must be followed by a decision (B), and you can’t make another request until a decision is made.
		- The assistant submits a report (A), which is immediately approved by the manager (B), and then another report is submitted (A) and approved (B).
		- After a submission (A), there's a timely approval (B), followed by archiving.
		- The process involves submitting (A) → approval (B) → submission (A) → approval (B), with no skipped approvals.
	2. Some examples violating this constraint:
		- Two submissions (A) occur in a row before any approval (B) is given.
		- A submission (A) happens, then a discussion takes place, and another submission (A) occurs without any approval (B) in between.
		- A report is submitted (A), approved (B), then submitted again (A), but no second approval (B) follows.

- Init(a): A must be the first event in every process of execution. The process starts with A.
	1. Some examples satisfying this constraint:
		- A login (A) must be the first action in a session.
		- The user first starts a session (A), then proceeds to log in and access the dashboard.
		- The workflow begins when the system starts a session (A) before allowing the user to browse products.
		- A session is initiated (A), followed by profile viewing and editing.
	2. Some examples violating this constraint:
		- The user logs in (B) before the session is started (A).
		- Dashboard access occurs first (B), and the session start (A) is recorded later.
		- The flow begins with product browsing, not with session start (A) as required.

- not-responded-existence(A,B): If A occurs, then B must not occur anywhere in the process. The presence of A excludes B.
	1. Some examples satisfying this constraint:
		- If an emergency shutdown (A) occurs, then no restart (B) can happen in the same trace.
		- The fraud detection tool flags the account (A), and the team proceeds to suspend it without unlocking (B).
		- After an audit, the system flags an account (A), and a report is generated - no unlocking (B) happens.
		- The agent flags the account (A), which leads directly to closure (C), bypassing any unlock (B). 
	2. Some examples violating this constraint:
		- The system flags the account (A) and then later unlocks it (B) after user verification.
		- Following a flagging (A), the account is temporarily unlocked (B) to retrieve data.
		- The sequence B → A → C violates the constraint because both A and B happen within the same process.
		- The account is flagged (A) during review, and later unlocked (B) for continued use.

- not-response(A,B): If A happens, then B must not happen afterward. B is not allowed after A.
	1. Some examples satisfying this constraint:
		- If an invoice is canceled (A), no payment (B) should happen after.
		- The technician closes the ticket (A) and archives it without any further action.
		- After closing the ticket (A), the system logs the case as resolved with no reopening (B).
		- A ticket is closed (A) and followed by a feedback request, with no reopen (B) in the workflow.
		- The sequence B  A  C is allowed
	2. Some examples violating this constraint:
		- The ticket is closed (A) and then later reopened (B) due to a missed issue.
		- Closing (A) is followed by a user complaint, leading to a reopen (B).
		- After a ticket is closed (A), a second-level agent reopens it (B) for escalation.

- not-precedence(A,B): If B occurs, then A must not have occurred before. A must not precede B.
	1. Some examples satisfying this constraint:
		- If a refund is issued (B), it must not be preceded by a delivery (A).
		- The system issues a refund (B) automatically based on transaction failure, without any complaint submission (A) from the user.
		- A refund (B) is provided proactively during a recall process, with no customer complaints (A) involved.
		- The support team issues a refund (B) before any chance of submitting a complaint (A) by the user.
	2. Some examples violating this constraint:
		- The customer submits a complaint (A), and then the company issues a refund (B) in response.
		- After several complaint submissions (A), a refund (B) is processed.
		- A ticket involving a complaint (A) leads directly to a refund (B) approval.

- not-chain-response(A,B): It is forbidden that B occurs immediately after A. B must not directly follow A.
	1. Some examples satisfying this constraint:
		- After submitting a form (A), an approval (B) must not happen immediately.
		- The user saves a draft (A), reviews the data (C), and then submits the form (B).
		- After saving the draft (A), the document is edited (C) and only then submitted (B).
		- The process includes draft saving (A), a peer review, and finally form submission (B).
	2. Some examples violating this constraint:
		- The user saves the draft (A) and immediately submits the form (B).
		- Save draft (A) is followed directly by submission (B) without any checks.
		- A and B occur consecutively with no intermediate validation step.

- not-chain-precedence(A,B): If B occurs, it must not have been immediately preceded by A. A must not be directly before B.
	1. Some examples satisfying this constraint:
		- If a task is marked complete (B), it must not come right after a comment (A).
		- The system checks account balance (C), then grants access (B) - identity validation (A) was done earlier or skipped.
		- After completing a background check (C), the system grants access (B), not immediately after identity validation (A).
		- Access is granted (B) following a security questionnaire (C), with no direct preceding validation (A).
	2. Some examples violating this constraint:
		- The system validates identity (A) and immediately grants access (B).
		- A user passes identity check (A) and access is granted (B) right after, violating the constraint.
"""

    # Hirearchical relationships between constraints
    META_CONSTRAINTS = """These constraints are related together through hierarchical relationships. If a constraint implies one or more other constraints only the stronger (highest level) should be present in the final constraint list, so if for example if int he extracted list of constraints appear A, B and C but A implies B and B implies C then only A should be present in the final version of the constraints.+
Here follows all the implications:
- Chain-Succession implies Chain-response 
- Chain-Response implies Alternate-Response
- Alternate-Response implies Response
- Response implies Responded-Existence
- Chain-Succession implies Chain-Precedence
- Chain-Precedence implies Alternate-Precedence
- Alternate-Precedence implies Precedence
- Chain-Succession implies Alternate-Succession
- Alternate-Succession implies Succession
- Succession implies Co-Existence
- Co-Existence implies Responded-Existence
- Succession implies Response
- Succession implies Precedence
- Alternate-Succession implies Alternate-Response
- Alternate-Succession implies Alternate-Precedence
- Init implies Precedence
- Exclusive-Choice implies Choice
- Not-Exclusive-Choice implies Not-Succession
- Not-Succession implies Not-Chain-Succession
"""

    # Formatting instructions and process description
    DESCRIPTION_AND_FORMATTING_INFORMATION = """The activities should not be shortened to a letter but included in the final constraint in a simplified version, such as executed_payment, approval_request, confirmation, ...
In our final interaction the constraint should be defined as "Final Formal Declarative Constraints: " (this line MUST appear only once in your reply, if you have any intermediate interpretations you can use "Temporary Declarative Constraints" or similar phrases) followed by one constraint per line defined using the template provided in the previous instruction.
Furthermore, in a line, you have to summarize all the activities present in the constraints, writing it as "Activities: " and on the same line, all the activities divided by commas, you cannot put a dot at the end of the line
Be succinct and do not hallucinate.
{interaction_status}

Here is the process description:
{textual_description}
"""