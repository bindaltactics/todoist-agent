AI Task Management Layer — Simple Requirements List

1. Task intake

* The system must detect when a task is created.
* The system must detect when a task is updated.
* The system must detect when a task is completed.
* The system must detect when a task becomes overdue.
* The system must capture task title, description, status, priority, due date, project, section, labels, and comments.
* The system must keep enough history to understand how a task has changed over time.

⸻

2. Task classification

* The system must classify each task by priority.
* The system must classify each task by project.
* The system must classify each task by section/status.
* The system must classify each task by task type, such as admin, deep work, follow-up, errand, communication, research, or planning.
* The system must estimate task effort.
* The system must estimate urgency.
* The system must estimate importance.
* The system must identify whether the task is vague or actionable.
* The system must identify whether the task needs clarification from the user.

⸻

3. Task planning

* The system must help turn vague tasks into clear tasks.
* The system must suggest a better task title when required.
* The system must suggest the next best action.
* The system must suggest subtasks for larger tasks.
* The system must identify missing information needed to progress the task.
* The system must ask targeted clarification questions.
* The system must suggest due dates when appropriate.
* The system must suggest reminders when appropriate.
* The system must avoid over-planning simple tasks.

⸻

4. Task validation

* The system must check whether a task is clear enough to action.
* The system must flag tasks that are too vague.
* The system must flag tasks with no obvious next step.
* The system must flag tasks that are overdue.
* The system must flag tasks that are stale or inactive.
* The system must flag tasks that are blocked.
* The system must flag tasks with missing or unrealistic dates.
* The system must flag possible duplicate tasks.
* The system must validate AI-suggested actions before they are applied.

⸻

5. Comment-based interaction

* The system must allow the user to interact with the AI through task comments.
* The system must understand comments as instructions, questions, answers, or status updates.
* The system must respond to user questions in the task comments.
* The system must take action based on clear user instructions in comments.
* The system must ask follow-up questions in comments when more information is needed.
* The system must provide task-specific guidance in comments.
* The system must be able to draft text, plans, or next steps based on the task context.
* The system must confirm actions taken through comments.
* The system must avoid cluttering the task with unnecessary comments.

⸻

6. Supported user actions through comments

The system must support requests like:

* Plan this task.
* Break this into smaller steps.
* What should I do next?
* Set this due date.
* Change the priority.
* Move this to another project or section.
* Mark this as blocked.
* Remind me later.
* Draft an email/message/document for this.
* Rewrite this task more clearly.
* Ask me questions to help complete this.
* Summarise the task context.
* Provide input or suggestions on the task.

⸻

7. AI agents / capabilities

The system must include these logical capabilities:

Planning capability

* Helps structure the task and create an execution plan.

Solution capability

* Helps the user actually complete the task.

Validation capability

* Checks task quality and AI action safety.

Classification capability

* Categorises and prioritises tasks.

Conversation capability

* Understands and manages comment-based interaction.

Notification capability

* Decides when to nudge, remind, or ask the user something.

⸻

8. Notifications

* The system must notify the user when the AI has a question.
* The system must notify the user when a high-priority task needs attention.
* The system must notify the user when a task is due soon.
* The system must notify the user when a task is overdue.
* The system must notify the user when a blocked task needs follow-up.
* The system must notify the user when a vague task needs clarification.
* The system must support reminder-style notifications.
* The system must support follow-up notifications when the user has not responded.
* The system must avoid sending too many notifications.
* The system must support quiet hours or notification suppression.

⸻

9. Task state management

* The system must track whether a task is new, classified, planned, blocked, waiting, stale, clarified, or completed.
* The system must track whether the AI is waiting for the user to respond.
* The system must track what question the AI asked.
* The system must track whether the user answered the AI’s question.
* The system must track when a follow-up is needed.
* The system must track when the AI last processed the task.
* The system must track when the user last interacted with the task.

⸻

10. Safety and control

* The system must not delete tasks automatically.
* The system must not complete tasks automatically unless the user explicitly requests it.
* The system must not make high-risk changes without clear user instruction.
* The system must prefer suggestions over automatic changes when confidence is low.
* The system must validate actions before applying them.
* The system must keep a record of AI actions.
* The system must prevent repeated or duplicate actions.
* The system must prevent repeated questions.
* The system must allow the user to override or correct AI decisions.

⸻

11. Learning and improvement

* The system should learn from completed tasks.
* The system should learn from user corrections.
* The system should improve future classification based on user behaviour.
* The system should improve reminder timing based on completion patterns.
* The system should track which AI suggestions were accepted or ignored.
* The system should identify recurring task patterns over time.

⸻

12. Daily review

* The system must provide a daily task review.
* The system must highlight overdue tasks.
* The system must highlight high-priority tasks.
* The system must highlight unclear tasks.
* The system must highlight blocked tasks.
* The system must highlight unanswered AI questions.
* The system must suggest the top tasks to focus on.
* The system must provide a concise planning summary.

⸻

13. User preferences

* The system must support user-specific rules.
* The system must support preferred notification times.
* The system must support quiet hours.
* The system must support preferred planning style.
* The system must support automatic versus approval-based actions.
* The system must support preferred project/section mapping.
* The system must support reminder preferences.

⸻

14. Audit and transparency

* The system must record what the AI suggested.
* The system must record what the AI changed.
* The system must record why an action was taken.
* The system must record confidence levels for AI decisions.
* The system must record when notifications were sent.
* The system must record when clarification questions were asked and answered.
* The system must make it possible to review AI activity later.

⸻

15. Reliability

* The system must avoid processing the same event twice.
* The system must handle failed updates safely.
* The system must recover from temporary integration failures.
* The system must avoid creating duplicate comments, reminders, or subtasks.
* The system must keep task state consistent.
* The system must support retries for failed operations.
* The system must handle incomplete or missing task data gracefully.

⸻

16. Minimum viable requirements

For the first usable version, the system only needs to:

* Detect new and updated tasks.
* Classify priority, project, section, and task type.
* Detect vague tasks.
* Ask clarification questions in comments.
* Respond to user comments.
* Support simple commands like plan, next step, blocked, due date, and reminder.
* Track pending AI questions.
* Send notifications for unanswered questions.
* Provide a daily review summary.
* Keep an audit trail of AI actions.