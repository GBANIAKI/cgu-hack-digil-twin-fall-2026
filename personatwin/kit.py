"""Fixed Common Kit content supplied for PersonaTwin AI. Do not change wording or key."""
ITEMS = {
    "B01": "Am the life of the party.", "B02": "Feel little concern for others.",
    "B03": "Am always prepared.", "B04": "Get stressed out easily.",
    "B05": "Have a rich vocabulary.", "B06": "Don't talk a lot.",
    "B07": "Am interested in people.", "B08": "Leave my belongings around.",
    "B09": "Am relaxed most of the time.", "B10": "Have difficulty understanding abstract ideas.",
    "B11": "Feel comfortable around people.", "B12": "Insult people.",
    "B13": "Pay attention to details.", "B14": "Worry about things.",
    "B15": "Have a vivid imagination.", "B16": "Keep in the background.",
    "B17": "Sympathize with others' feelings.", "B18": "Make a mess of things.",
    "B19": "Seldom feel blue.", "B20": "Am not interested in abstract ideas.",
    "B21": "Start conversations.", "B22": "Am not interested in other people's problems.",
    "B23": "Get chores done right away.", "B24": "Am easily disturbed.",
    "B25": "Have excellent ideas.", "B26": "Have little to say.",
    "B27": "Have a soft heart.", "B28": "Often forget to put things back in their proper place.",
    "B29": "Get upset easily.", "B30": "Do not have a good imagination.",
    "B31": "Talk to a lot of different people at parties.", "B32": "Am not really interested in others.",
    "B33": "Like order.", "B34": "Change my mood a lot.",
    "B35": "Am quick to understand things.", "B36": "Don't like to draw attention to myself.",
    "B37": "Take time out for others.", "B38": "Shirk my duties.",
    "B39": "Have frequent mood swings.", "B40": "Use difficult words.",
    "B41": "Don't mind being the center of attention.", "B42": "Feel others' emotions.",
    "B43": "Follow a schedule.", "B44": "Get irritated easily.",
    "B45": "Spend time reflecting on things.", "B46": "Am quiet around strangers.",
    "B47": "Make people feel at ease.", "B48": "Am exacting in my work.",
    "B49": "Often feel blue.", "B50": "Am full of ideas.",
}
DOMAINS = {
    "Extraversion": (["B01", "B11", "B21", "B31", "B41"], ["B06", "B16", "B26", "B36", "B46"]),
    "Agreeableness": (["B07", "B17", "B27", "B37", "B42", "B47"], ["B02", "B12", "B22", "B32"]),
    "Conscientiousness": (["B03", "B13", "B23", "B33", "B43", "B48"], ["B08", "B18", "B28", "B38"]),
    "Emotional Stability": (["B09", "B19"], ["B04", "B14", "B24", "B29", "B34", "B39", "B44", "B49"]),
    "Intellect/Imagination": (["B05", "B15", "B25", "B35", "B40", "B45", "B50"], ["B10", "B20", "B30"]),
}
DOMAIN_TEXT = {
    "Extraversion": {"higher": "describes themselves as outgoing, comfortable starting conversations and being noticed", "middle": "describes themselves as neither especially outgoing nor especially reserved", "lower": "describes themselves as more reserved, quieter around new people, and less drawn to attention"},
    "Agreeableness": {"higher": "describes themselves as warm, attentive to other people's feelings, and willing to make time for others", "middle": "describes themselves as moderately attentive to other people's feelings and needs", "lower": "describes themselves as less focused on other people's feelings and problems"},
    "Conscientiousness": {"higher": "describes themselves as organized, prepared, and careful with details", "middle": "describes themselves as moderately organized, structured in some areas and relaxed in others", "lower": "describes themselves as less structured and more relaxed about order and schedules"},
    "Emotional Stability": {"higher": "describes themselves as usually calm and not easily stressed", "middle": "describes themselves as sometimes calm and sometimes stressed or worried", "lower": "describes themselves as more easily stressed or worried, with moods that shift more often"},
    "Intellect/Imagination": {"higher": "describes themselves as enjoying ideas, reflection, and imagination", "middle": "describes themselves as moderately drawn to ideas and imagination", "lower": "describes themselves as more practical and less drawn to abstract ideas"},
}
SCENARIOS = {
    "S01": {"wording": "In a planning meeting your manager proposes a deadline you are fairly sure the team cannot hit. Everyone else nods.", "options": {"A": "Say so in the meeting and give your reasons.", "B": "Go along in the meeting and raise it with your manager privately afterwards.", "C": "Go along and plan to put in extra hours to try to hit it.", "D": "Ask a question in the meeting that points at the risk without saying you disagree."}, "patterns": {"A": "raises disagreement openly and in the moment, even in front of the group", "B": "raises disagreement, but privately rather than in front of the group", "C": "absorbs the cost personally rather than push back", "D": "signals concerns indirectly rather than disagreeing outright"}},
    "S03": {"wording": "Late on a Friday, something you shipped starts failing for some customers. Undoing it removes a feature they asked for. A fix might take one hour or four. Your lead is unreachable.", "options": {"A": "Undo it now and fix it properly next week.", "B": "Try the fix, but undo it if it is not working within an hour.", "C": "Keep trying to reach your lead before doing anything.", "D": "Spend 20 minutes finding out how many customers are affected, then decide."}, "patterns": {"A": "prefers the safe, reversible option under pressure", "B": "takes a bounded risk with a clear time limit and a fallback", "C": "prefers to get sign-off from authority before acting", "D": "gathers information before committing to a decision"}},
    "S05": {"wording": "In a meeting a colleague presents an idea that was mostly yours. They do not mention you.", "options": {"A": "Say in the meeting that you had worked on this with them.", "B": "Talk to them privately afterwards.", "C": "Let it go. The idea moving forward is what matters.", "D": "Make sure your manager knows, without confronting the colleague."}, "patterns": {"A": "claims credit openly in the moment", "B": "addresses the issue one-to-one with the person directly", "C": "puts the outcome ahead of personal credit", "D": "goes through the manager rather than confronting the colleague"}},
}
WRITING = {"W01": "You have to tell your team that a project they worked hard on has been cancelled. Write the message you would post.", "W03": "Someone shares an idea in the team chat that you think is genuinely great. Reply."}
BUILD_IDS = set(ITEMS) | set(SCENARIOS) | set(WRITING)
TEST_IDS = {"S02", "S04", "S06", "W02", "W04"}
