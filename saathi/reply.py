"""Fixed reply templates in English and Gujarati, filled only from the facts.

This is the no-LLM "phrase" step (PLAN.md section 1, step 4 fallback). Every
number in a reply is read from the facts dict that `assistant.compute` built;
nothing here calculates. Replies are short, because she reads them on a basic
phone, and they describe patterns, never people.
"""
from .actions import render_action
from .lang import SUBJECTS, class_name, date_text, grades_text, join, month_name

W = {  # every sentence, in both languages
    # --- shared ---
    "do": ("Do", "શું કરવું"),
    "why": ("Why", "કારણ"),
    "days_ago": ("{d} days ago", "{d} દિવસ પહેલાં"),
    "days": ("{d} days", "{d} દિવસ"),
    "never_visited": ("no visit recorded", "કોઈ મુલાકાત નોંધાઈ નથી"),
    "no_data": ("no data", "માહિતી નથી"),
    # The score is always named "need for help": a bare "78/100" reads like good marks (D-034).
    "score": ("need for help {s}/100", "મદદની જરૂર {s}/100"),
    "priority": ("{p} priority", "{p} પ્રાથમિકતા"),
    "higher_score": ("Need for help: the higher the number, the sooner the school needs support.",
                     "મદદની જરૂર: આંકડો જેટલો વધુ, તેટલી શાળાને વહેલી મદદની જરૂર."),
    "cause_caveat": ("The data cannot show the exact cause; check this on your visit.",
                     "માહિતી પરથી ચોક્કસ કારણ કહી શકાય નહીં; મુલાકાત વખતે તપાસ કરો."),
    "more": ("+{n} more", "+{n} વધુ"),
    # --- reasons a school is flagged ---
    "r_learning_level": ("average marks {v}%", "સરેરાશ ગુણ {v}%"),
    "r_below_basic": ("{v}% of children below basic level", "{v}% બાળકો પાયાના સ્તરથી નીચે"),
    "r_student_attendance": ("attendance {v}%", "હાજરી {v}%"),
    # A change is said as before and after, never in "points": she should not have to subtract (D-035).
    "r_attendance_drop": ("attendance fell from {prev}% to {now}%", "હાજરી {prev}%થી ઘટીને {now}%"),
    "r_attendance_with_drop": ("attendance fell from {prev}% to {v}%", "હાજરી {prev}%થી ઘટીને {v}%"),
    # --- month notes ---
    "using_latest": ("{month} data, the latest available", "{month}ની માહિતી મુજબ"),
    "using_month": ("{month} data", "{month}ની માહિતી મુજબ"),
    "m_too_early": ("A score needs two earlier school months, so {first} is the first month that can be scored. "
                    "Showing {latest}.",
                    "સ્કોર માટે અગાઉના બે શાળા-મહિનાની માહિતી જોઈએ, તેથી પહેલો સ્કોર {first}નો મળે. "
                    "{latest}ની માહિતી બતાવી છે."),
    "none_scored": ("No school could be scored for {month}.", "{month} માટે કોઈ શાળાનો સ્કોર આપી શકાયો નથી."),
    "m_school_closed": ("Schools were closed in {month} for {note}, so there is no data for that month.",
                        "{month}માં શાળાઓ બંધ હતી (વેકેશન), તેથી તે મહિનાની માહિતી નથી."),
    "m_not_yet": ("{month} data is not available yet. Showing {latest}, the latest month.",
                  "{month}ની માહિતી હજી આવી નથી, તેથી છેલ્લા મહિના ({latest})ની માહિતી બતાવી છે."),
    "m_before_data": ("This data starts in {first}, so there is nothing for {month}. Showing {latest}.",
                      "આ માહિતી {first}થી શરૂ થાય છે, તેથી {month}ની માહિતી નથી. {latest}ની માહિતી બતાવી છે."),
    # --- top priority schools ---
    "top_header": ("Schools to visit first ({using}):", "સૌથી પહેલાં મુલાકાત લેવાની શાળાઓ ({using}):"),
    "last_visit_short": ("Last visit: {when}", "છેલ્લી મુલાકાત: {when}"),
    "last_visit_paren": ("(last visit {when})", "(છેલ્લી મુલાકાત {when})"),
    "only_n_need": ("Only {n} schools need extra support in {month}; the rest are Low priority.",
                    "{month}માં ફક્ત {n} શાળાઓને વધારાની મદદની જરૂર છે; બાકીની શાળાઓ ઓછી પ્રાથમિકતામાં છે."),
    "none_need": ("No school needs extra support in {month}: all scored schools are Low priority.",
                  "{month}માં કોઈ શાળાને વધારાની મદદની જરૂર નથી: બધી શાળાઓ ઓછી પ્રાથમિકતામાં છે."),
    "also": ("Also:", "આ પણ જુઓ:"),
    "moved_down": ("{name} ({p}, need for help {s}) was visited {d} days ago, so it is lower on this list. "
                   "Follow up by phone.",
                   "{name} ({p}, મદદની જરૂર {s}): {d} દિવસ પહેલાં જ મુલાકાત લીધી છે, તેથી યાદીમાં નીચે રાખી છે. "
                   "ફોન પર ફોલો-અપ કરો."),
    "watch_class": ("{name}: Low priority overall, but {cls} is {v}%. Worth a short visit.",
                    "{name}: એકંદરે ઓછી પ્રાથમિકતા, પણ {cls}માં {v}% છે. ટૂંકી મુલાકાત લેવી યોગ્ય રહેશે."),
    "watch_other": ("{name}: Low priority overall, but: {action}", "{name}: એકંદરે ઓછી પ્રાથમિકતા, પણ: {action}"),
    "not_enough_line": ("{name}: not enough {month} data to score. {action}",
                        "{name}: {month}ની પૂરતી માહિતી ન હોવાથી સ્કોર આપ્યો નથી. {action}"),
    "long_unvisited": ("Not visited for over {n} days: {list}", "{n} દિવસથી વધુ સમયથી મુલાકાત લીધી નથી: {list}"),
    "ask_more": ('Ask "{q}" for details.', 'વિગત માટે પૂછો: "{q}"'),
    "q_about": ("Tell me about {name}", "{name} વિશે જણાવો"),
    # --- the visit plan as cards on the page (plain words, the same terms as the home screen) ---
    "cards_title": ("Visit these schools first", "પહેલાં આ શાળાઓની મુલાકાત લો"),
    "cards_sub": ("{month} {year} data. Need for help is out of 100: the higher it is, the sooner the school needs help.",
                  "{month} {year}ની માહિતી. મદદની જરૂર 100માંથી: આંકડો જેટલો વધુ, તેટલી શાળાને વહેલી મદદની જરૂર."),
    "lbl_High": ("Needs help first", "પહેલાં મદદની જરૂર"),
    "lbl_Medium": ("Keep an eye on", "ધ્યાન રાખો"),
    "lbl_Low": ("Doing fine", "બરાબર ચાલે છે"),
    "also_keep": ("Also keep in mind", "આ પણ ધ્યાનમાં રાખો"),
    "q_attendance": ("Show attendance for {name}", "{name}ની હાજરી બતાવો"),
    "q_gaps": ("Which data is missing for {name}?", "{name}ની કઈ માહિતી ખૂટે છે?"),
    # --- school summary ---
    "type_primary": ("primary school", "પ્રાથમિક શાળા"),
    "type_upper_primary": ("upper primary school", "ઉચ્ચ પ્રાથમિક શાળા"),
    "summary_header": ("{name} ({type}, {n} children), {month}", "{name} ({type}, {n} બાળકો), {month}"),
    "priority_line": ("Priority: {p}, need for help {s}/100", "પ્રાથમિકતા: {p}, મદદની જરૂર {s}/100"),
    "attendance_line": ("Attendance {v}% (previous {k} months: {prev}%); teachers {t}",
                        "બાળકોની હાજરી {v}% (અગાઉના {k} મહિનાની સરેરાશ {prev}%); શિક્ષકોની હાજરી {t}"),
    "learning_line": ("Learning: average {v}%, {b}% below basic ({r} of {e} class results)",
                      "અધ્યયન: સરેરાશ ગુણ {v}%, {b}% બાળકો પાયાના સ્તરથી નીચે ({e}માંથી {r} વર્ગનાં પરિણામ)"),
    "lowest_class": ("Lowest class: {cls} {v}%", "સૌથી ઓછા ગુણ: {cls}માં {v}%"),
    "facilities": ("School facts ({date}): {list}", "શાળાની વિગત ({date} મુજબ): {list}"),
    "f_posts": ("{n} of {m} teacher posts filled", "શિક્ષકોની {m}માંથી {n} જગ્યા ભરાયેલી"),
    "f_multigrade": ("multigrade classes", "એક ઓરડામાં એકથી વધુ ધોરણ ભણે છે"),
    "f_drinking_water": ("drinking water not functional", "પીવાનું પાણી ચાલુ નથી"),
    "f_girls_toilet": ("girls' toilet not functional", "કન્યા શૌચાલય ચાલુ નથી"),
    "f_missing": ("{field} not recorded", "{field}ની માહિતી નથી"),
    "last_visit_line": ("Last visit: {date} ({d} days ago): {note}", "છેલ્લી મુલાકાત: {date} ({d} દિવસ પહેલાં): {note}"),
    "not_enough_header": ("Not enough {month} data to give a score. Please check:",
                          "{month}ની પૂરતી માહિતી નથી, તેથી સ્કોર આપી શકાતો નથી. કૃપા કરીને તપાસો:"),
    # --- subject analysis ---
    "subject_header": ("{name}, {cls}, {month}: average {v}%{bb}.", "{name}, {cls} ({month}): સરેરાશ ગુણ {v}%{bb}."),
    "bb_long": (", {b}% of children below basic", ", {b}% બાળકો પાયાના સ્તરથી નીચે"),
    "bb_short": (" ({b}% below basic)", " ({b}% પાયાથી નીચે)"),
    "latest_is_old": ("This is the latest result; {missing} has not arrived.",
                      "આ છેલ્લું પરિણામ છે; {missing}નું પરિણામ આવ્યું નથી."),
    "trend": ("Trend: {list}", "વલણ: {list}"),
    "change_down": ("lower than in {m}", "{m} કરતાં ઓછું"),
    "change_up": ("higher than in {m}", "{m} કરતાં વધુ"),
    "change_none": ("no change since {m}", "{m}થી કોઈ ફેરફાર નથી"),
    "same_class": ("Same class, other subjects: {list}", "આ જ ધોરણના બીજા વિષયો: {list}"),
    "cluster_avg": ("Cluster average for {cls}: {v}% ({n} schools){cmp}", "{cls}ની ક્લસ્ટર સરેરાશ: {v}% ({n} શાળા){cmp}"),
    "cmp_below": ("; this class, at {v}%, is below it", "; આ વર્ગ {v}% સાથે તેનાથી નીચે છે"),
    "cmp_above": ("; this class, at {v}%, is above it", "; આ વર્ગ {v}% સાથે તેનાથી ઉપર છે"),
    "cmp_same": ("; this class is at the average", "; આ વર્ગ સરેરાશ જેટલો જ છે"),
    "visit_notes": ("Visit notes:", "મુલાકાતની નોંધ:"),
    "na_grade_not_assessed": ("Only Grades {grades} are assessed in this data, so there are no Grade {g} results.",
                              "આ માહિતીમાં ફક્ત ધોરણ {grades}નું મૂલ્યાંકન છે, તેથી ધોરણ {g}નું પરિણામ નથી."),
    "na_grade_not_offered": ("{name} is a {type}, so it has no Grade {g}. Results are available for Grades {grades}.",
                             "{name} {type} છે, તેથી ત્યાં ધોરણ {g} નથી. ધોરણ {grades}નાં પરિણામ ઉપલબ્ધ છે."),
    "na_subject_not_at_school": ("{name} is a {type}: its classes take {instead}, not {subject}.",
                                 "{name} {type} છે: ત્યાં {subject} નહીં, {instead} ભણાવાય છે."),
    "na_subject_not_taught": ("Grade {g} takes {instead}, not {subject}.",
                              "ધોરણ {g}માં {subject} નહીં, {instead} ભણાવાય છે."),
    "no_results_any_month": ("No {cls} results for {name} in any month. Please check with the head teacher.",
                             "{name}નું {cls}નું કોઈ પણ મહિનાનું પરિણામ નથી. કૃપા કરીને આચાર્ય સાથે ખાતરી કરો."),
    # --- class across the cluster ---
    "label_all_grades": ("{subject} (all grades)", "{subject} (બધાં ધોરણ)"),
    "label_all_subjects": ("Grade {g} (all subjects)", "ધોરણ {g} (બધા વિષય)"),
    "label_all_classes": ("All classes", "બધા વર્ગ"),
    "class_header": ("{label} across the cluster, {month}: average {v}% ({n} class results).",
                     "આખા ક્લસ્ટરમાં {label} ({month}): સરેરાશ ગુણ {v}% ({n} વર્ગનાં પરિણામ)."),
    "below_concern": ("{c} of {n} are below {p}%. Lowest:", "{n}માંથી {c} વર્ગમાં {p}%થી ઓછા ગુણ છે. સૌથી ઓછા ગુણ:"),
    "lowest_only": ("Lowest:", "સૌથી ઓછા ગુણ:"),
    "class_row": ("{name}{cls}: {v}%{bb}", "{name}{cls}: {v}%{bb}"),
    "no_result": ("No {month} result: {list}", "{month}નું પરિણામ આવ્યું નથી: {list}"),
    "ask_one_school": ('For one school, ask: "{q}"', 'એક શાળા માટે પૂછો: "{q}"'),
    "q_subject": ("Why is {cls} low in {name}?", "{name}માં {cls} કેમ ઓછું છે?"),
    # --- attendance ---
    "att_school_header": ("{name} attendance (children / teachers):", "{name}ની હાજરી (બાળકો / શિક્ષકો):"),
    "att_month": ("{month}: {s} / {t}", "{month}: {s} / {t}"),
    "att_closed": ("{month}: school closed for {note}", "{month}: શાળા બંધ (વેકેશન)"),
    "att_missing": ("{month}: no record", "{month}: માહિતી આવી નથી"),
    "att_lower": ("{month} ({now}%) is lower than the previous {k} months ({prev}%).",
                  "{month}ની હાજરી ({now}%) અગાઉના {k} મહિના ({prev}%) કરતાં ઓછી છે."),
    "att_higher": ("{month} ({now}%) is higher than the previous {k} months ({prev}%).",
                   "{month}ની હાજરી ({now}%) અગાઉના {k} મહિના ({prev}%) કરતાં વધુ છે."),
    "att_same": ("{month} is the same as the previous {k} months ({prev}%).",
                 "{month}ની હાજરી અગાઉના {k} મહિના જેટલી જ છે ({prev}%)."),
    "att_cluster_line": ("Cluster, {month}: {v}% ({r} of {t} schools reported).",
                         "ક્લસ્ટરની સરેરાશ ({month}): {v}% ({t}માંથી {r} શાળાની માહિતી)."),
    "att_no_record": ("No attendance record for {name} in {month}: the data has not arrived. "
                      "Please check with the head teacher.",
                      "{name} શાળાની {month} મહિનાની હાજરી હજી આવી નથી. કૃપા કરીને આચાર્ય સાથે વાત કરીને ખાતરી કરો."),
    "att_children_missing": ("Children's attendance for {name} in {month} is missing. Please check with the head teacher.",
                             "{name} શાળાની {month} મહિનાની બાળકોની હાજરી ખૂટે છે. કૃપા કરીને આચાર્ય સાથે વાત કરીને ખાતરી કરો."),
    "att_asked": ("{name}, {month}: children {s}, teachers {t}.", "{name}, {month}: બાળકો {s}, શિક્ષકો {t}."),
    "att_cluster_header": ("Cluster attendance (average of schools that reported):",
                           "ક્લસ્ટરની હાજરી (માહિતી આપનાર શાળાઓની સરેરાશ):"),
    "att_cluster_month": ("{month}: {v}% ({r}/{t} schools)", "{month}: {v}% ({r}/{t} શાળા)"),
    "att_drops": ("Biggest falls in {month}:", "{month}માં સૌથી વધુ ઘટાડો:"),
    "att_drop_row": ("{name}: fell from {prev}% to {s}%", "{name}: {prev}%થી ઘટીને {s}%"),
    "att_teacher_low": ("Teacher attendance below {p}%: {list}. This can be leave, training or official duty; "
                        "worth a conversation with the head teacher.",
                        "શિક્ષકોની હાજરી {p}%થી ઓછી: {list}. રજા, તાલીમ કે સરકારી ફરજને કારણે હોઈ શકે; "
                        "આચાર્ય સાથે વાત કરવા જેવી છે."),
    "att_not_reported": ("No {month} record: {list}", "{month}ની માહિતી આવી નથી: {list}"),
    # --- missing data ---
    "gaps_header": ("Data gaps (as of {date}): {n} of {t} schools have at least one gap.",
                    "ખૂટતી માહિતી ({date} સુધી): {t}માંથી {n} શાળામાં કંઈક ખૂટે છે."),
    "gaps_not_enough": ("Not enough data to score {month}:", "{month}નો સ્કોર આપવા પૂરતી માહિતી નથી:"),
    "gaps_other": ("Other gaps, most recent first:", "બીજી ખૂટતી માહિતી (નવી પહેલાં):"),
    "gaps_also": ("Smaller or older gaps also at: {list}", "નાની કે જૂની ખૂટતી માહિતી આ શાળાઓમાં પણ: {list}"),
    "gaps_closed": ("{months}: schools were closed, so that is not missing data.",
                    "{months}માં શાળાઓ બંધ હતી, તે ખૂટતી માહિતી ગણાતી નથી."),
    "gaps_school_header": ("Data gaps for {name}:", "{name}ની ખૂટતી માહિતી:"),
    "gaps_school_none": ("No data gaps for {name}: every school month is complete.",
                         "{name}ની કોઈ માહિતી ખૂટતી નથી: શાળાના બધા મહિના પૂરા છે."),
    "g_attendance_row": ("no attendance record for {month}", "{month}ની હાજરી આવી નથી"),
    "g_student_attendance": ("children's attendance missing for {month}", "{month}ની બાળકોની હાજરી ખૂટે છે"),
    "g_teacher_attendance": ("teacher attendance missing for {month}", "{month}ની શિક્ષકોની હાજરી ખૂટે છે"),
    "g_assessment_results": ("{a} of {e} results for {month}", "{month}: {e}માંથી {a} પરિણામ આવ્યાં"),
    "g_below_basic_class": ("below-basic share missing for {cls} in {month}", "{month}માં {cls}નો પાયાથી નીચેનો આંકડો ખૂટે છે"),
    "g_below_basic": ("below-basic share for {a} of {e} results in {month}", "{month}: {e}માંથી ફક્ત {a} પરિણામમાં પાયાથી નીચેનો આંકડો છે"),
    "g_attendance_history": ("only {a} of the previous {e} months of attendance", "અગાઉના {e} મહિનામાંથી ફક્ત {a} મહિનાની હાજરી"),
    "g_facilities": ("{field} not recorded", "{field}ની માહિતી નથી"),
    # --- visits ---
    "visit_last": ("Last visit to {name}: {date} ({d} days ago), focus: {focus}.",
                   "{name}ની છેલ્લી મુલાકાત: {date} ({d} દિવસ પહેલાં), વિષય: {focus}."),
    "visit_note": ("Note: {note}", "નોંધ: {note}"),
    "visit_earlier": ("Earlier: {list}", "અગાઉ: {list}"),
    "visit_none": ("No visits to {name} are recorded.", "{name}ની કોઈ મુલાકાત નોંધાઈ નથી."),
    "visits_30": ("Visits in the last {w} days: {n}.", "છેલ્લા {w} દિવસમાં મુલાકાતો: {n}."),
    "visits_longest": ("Not visited for longest:", "સૌથી લાંબા સમયથી મુલાકાત બાકી:"),
    "visit_row": ("{name}: {d} days ({date})", "{name}: {d} દિવસ ({date})"),
    "visit_row_never": ("{name}: no visit recorded", "{name}: કોઈ મુલાકાત નોંધાઈ નથી"),
    "ask_visit": ('For notes, ask: "When did I last visit {name}?"', 'નોંધ માટે પૂછો: "{name}ની છેલ્લી મુલાકાત ક્યારે હતી?"'),
    # --- the whole cluster (D-037) ---
    "list_header": ("Your {n} schools, {month} (need for help out of 100: the higher it is, the sooner the school needs help):",
                    "તમારી {n} શાળાઓ, {month} (મદદની જરૂર 100માંથી: આંકડો જેટલો વધુ, તેટલી શાળાને વહેલી મદદની જરૂર):"),
    "list_group": ("{label} ({n}): {list}", "{label} ({n}): {list}"),
    "lbl_waiting": ("Waiting for data", "માહિતી આવવાની બાકી"),
    "list_types_header": ("Your {n} schools: {p} primary and {u} upper primary.", "તમારી {n} શાળાઓ: {p} પ્રાથમિક અને {u} ઉચ્ચ પ્રાથમિક."),
    "lbl_primary": ("Primary", "પ્રાથમિક"),
    "lbl_upper_primary": ("Upper primary", "ઉચ્ચ પ્રાથમિક"),
    "visits_recent": ("Schools visited in the last {w} days: {list}", "છેલ્લા {w} દિવસમાં મુલાકાત લીધેલી શાળાઓ: {list}"),
    # --- officer summary ---
    "off_header": ("Cluster update, {month} {year} ({t} schools)", "ક્લસ્ટર અહેવાલ, {month} {year} ({t} શાળા)"),
    "off_counts": ("Priority: {h} High, {m} Medium, {l} Low; {n} with not enough data.",
                   "પ્રાથમિકતા: {h} ઉચ્ચ, {m} મધ્યમ, {l} ઓછી; {n} શાળાની પૂરતી માહિતી નથી."),
    "off_school": ("{name} (need for help {s}/100): {reason}", "{name} (મદદની જરૂર {s}/100): {reason}"),
    "off_medium": ("Medium: {list}", "મધ્યમ: {list}"),
    "off_attendance": ("Cluster attendance: {v}% ({r} of {t} schools reported).",
                       "ક્લસ્ટર હાજરી: {v}% ({t}માંથી {r} શાળાની માહિતી)."),
    "off_data": ("Data: {month} data from {list} has not arrived; I will follow up with the school.",
                 "માહિતી: {list}ની {month}ની માહિતી આવી નથી; હું શાળા સાથે ફોલો-અપ કરીશ."),
    "off_plan": ("Plan this week: visit {list}.", "આ અઠવાડિયાનું આયોજન: {list}ની મુલાકાત."),
    "off_phone": ("Phone follow-up: {name} (visited {d} days ago).", "ફોન ફોલો-અપ: {name} ({d} દિવસ પહેલાં મુલાકાત લીધી છે)."),
    "off_watch": ("Also checking: {list}.", "આ પણ તપાસીશ: {list}."),
    # --- help, boundaries ---
    "help": ("I can help with your schools' attendance, learning results and visits. You can ask:",
             "હું તમારી શાળાઓની હાજરી, પરિણામ અને મુલાકાતો વિશે મદદ કરી શકું છું. આ રીતે પૂછો:"),
    "out_of_scope": ("I can only help with your schools: attendance, learning results, visits and what to do next.",
                     "હું ફક્ત તમારી શાળાઓ વિશે મદદ કરી શકું છું: હાજરી, પરિણામ, મુલાકાતો અને આગળ શું કરવું."),
    "people_judgement": ("Teachers and head teachers are not rated or blamed here. The data shows school patterns, "
                         "and low teacher attendance can be leave, training or official duty. I can show you:",
                         "અહીં શિક્ષકો કે આચાર્યોનું મૂલ્યાંકન કે દોષારોપણ થતું નથી. માહિતી શાળાની પરિસ્થિતિ બતાવે છે, "
                         "અને શિક્ષકોની ઓછી હાજરી રજા, તાલીમ કે સરકારી ફરજને કારણે પણ હોઈ શકે. હું આ બતાવી શકું:"),
    "personal_info": ("Personal details of children or staff (names, phone numbers) are not shared here. "
                      "For children, the data has only class averages. I can show you:",
                      "બાળકો કે સ્ટાફની વ્યક્તિગત માહિતી (નામ, ફોન) અહીં આપવામાં આવતી નથી. "
                      "બાળકો માટે ફક્ત વર્ગની સરેરાશ માહિતી છે. હું આ બતાવી શકું:"),
    "not_allowed": ("The data and these rules cannot be changed here, and figures are never made up: "
                    "every number comes from the school records. You can ask:",
                    "અહીં માહિતી કે નિયમો બદલી શકાતા નથી, અને આંકડા ક્યારેય ઘડી કાઢવામાં આવતા નથી: "
                    "દરેક આંકડો શાળાના રેકોર્ડમાંથી જ આવે છે. આ રીતે પૂછો:"),
    "not_found": ('There is no school called "{name}" in your cluster.', 'તમારા ક્લસ્ટરમાં "{name}" નામની શાળા નથી.'),
    "did_you_mean": ("Did you mean: {list}?", "શું તમે આમાંથી કોઈ શાળા વિશે પૂછો છો: {list}?"),
    "your_schools": ("Your schools: {list}", "તમારી શાળાઓ: {list}"),
    "clarify_school": ("Which school do you mean?", "કઈ શાળા વિશે પૂછો છો?"),
    "one_at_a_time": ("I can look at one school at a time. Which one?", "એક સમયે એક શાળા જોઈ શકાય છે. કઈ શાળા?"),
    "reply_with_name": ("Reply with the school name.", "શાળાનું નામ લખીને જવાબ આપો."),
    "clarify_grade": ("Which grade? {name} has Grades {list}.", "કયું ધોરણ? {name}માં ધોરણ {list} છે."),
    "clarify_subject": ("Which subject for Grade {g}? {list}", "ધોરણ {g} માટે કયો વિષય? {list}"),
}

PRIORITY_WORD = {"High": ("High", "ઉચ્ચ"), "Medium": ("Medium", "મધ્યમ"), "Low": ("Low", "ઓછી")}
FOCUS = {"Classroom observation": "વર્ગ નિરીક્ષણ", "EVS/Science": "પર્યાવરણ/વિજ્ઞાન", "Attendance": "હાજરી",
         "Maths": "ગણિત", "Teacher support": "શિક્ષક સહયોગ", "Gujarati reading": "ગુજરાતી વાચન",
         "School management": "શાળા વ્યવસ્થાપન"}
FACILITY_NAME = {"teacher_posts_sanctioned": ("sanctioned teacher posts", "મંજૂર શિક્ષક જગ્યા"),
                 "teachers_in_position": ("teachers in position", "હાજર શિક્ષકો"),
                 "multigrade_classes": ("multigrade classes", "બહુધોરણ વર્ગ"),
                 "drinking_water": ("drinking water", "પીવાનું પાણી"), "girls_toilet": ("girls' toilet", "કન્યા શૌચાલય"),
                 "electricity": ("electricity", "વીજળી")}
NAME_SUFFIXES = (" Primary School", " Pay Center School", " પ્રાથમિક શાળા", " પે સેન્ટર શાળા")

EXAMPLES = {
    "en": ["Which 3 schools need my visit this week?", "Why is Grade 5 Maths low in Rampura?",
           "Tell me about Chandrapur", "Which schools have missing data?", "When did I last visit Sonpura?",
           "Summary for my block officer"],
    "gu": ["આ અઠવાડિયે કઈ 3 શાળાઓની મુલાકાત લેવી?", "રામપુરામાં ધોરણ 5 ગણિત કેમ ઓછું છે?", "ચંદ્રપુર વિશે જણાવો",
           "કઈ શાળાઓની માહિતી ખૂટે છે?", "સોનપુરાની છેલ્લી મુલાકાત ક્યારે હતી?", "બ્લોક અધિકારી માટે સારાંશ"],
}
MAX_GAPS_PER_SCHOOL = 3
MAX_GAP_SCHOOLS = 6
MAX_VISIT_ROWS = 5


def t(key, lang, **values):
    return W[key][0 if lang == "en" else 1].format(**values)


def short(item, lang):
    """'Haripar Primary School' -> 'Haripar' (village name), from any dict with name / name_gu."""
    name = item["name_gu"] if lang == "gu" else item["name"]
    for suffix in NAME_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def below_basic(value, lang, style):
    return "" if value is None else t(f"bb_{style}", lang, b=value)


def pct(value, lang):
    return t("no_data", lang) if value is None else f"{value}%"


def prio(label, lang):
    return PRIORITY_WORD[label][0 if lang == "en" else 1]


def month(m, lang):
    return month_name(m, lang)


def option(label, question, school_id=None):
    item = {"label": label, "question": question}
    if school_id:
        item["school_id"] = school_id
    return item


def example_options(lang, count=3):
    return [option(q, q) for q in EXAMPLES[lang][:count]]


# --- pieces used by several replies -------------------------------------------------------

def reasons_text(entry, lang, limit=3):
    """Why a school is flagged, biggest reason first. A low attendance and a fall in it are one phrase."""
    return "; ".join(reason_parts(entry, lang, limit))


def reason_parts(entry, lang, limit=3):
    names, ind = list(entry["reasons"]), entry["indicators"]
    merged = "student_attendance" in names and "attendance_drop" in names
    if merged:
        names.remove("attendance_drop")
    parts = []
    for name in names[:limit]:
        if name == "student_attendance" and merged:
            drop = ind["attendance_drop"]
            parts.append(t("r_attendance_with_drop", lang, v=ind[name]["value"], d=drop["value"],
                           prev=drop["previous_avg"]))
        else:
            parts.append(t(f"r_{name}", lang, v=ind[name]["value"], prev=ind[name].get("previous_avg"),
                           now=ind["student_attendance"]["value"]))
    return parts


def note_text(note):
    """'Summer vacation (4 May - 7 June)' -> 'summer vacation (4 May - 7 June)', to sit inside a sentence."""
    return note[:1].lower() + note[1:]


def gap_text(gap, lang):
    what = gap["what"]
    m = month(gap["month"], lang) if "month" in gap else ""
    if what == "assessment_results":
        return t("g_assessment_results", lang, a=gap["available"], e=gap["expected"], month=m)
    if what == "below_basic":
        if "class" in gap:
            return t("g_below_basic_class", lang, cls=class_name(*gap["class"], lang), month=m)
        return t("g_below_basic", lang, a=gap["available"], e=gap["expected"], month=m)
    if what == "attendance_history":
        return t("g_attendance_history", lang, a=gap["available"], e=len(gap["months"]))
    if what == "facilities":
        return t("g_facilities", lang, field=FACILITY_NAME[gap["field"]][0 if lang == "en" else 1])
    return t(f"g_{what}", lang, month=m)


def gaps_text(gaps, lang):
    gaps = sorted(gaps, key=lambda g: g.get("month", ""), reverse=True)   # most recent first
    parts = [gap_text(g, lang) for g in gaps[:MAX_GAPS_PER_SCHOOL]]
    if len(gaps) > MAX_GAPS_PER_SCHOOL:
        parts.append(t("more", lang, n=len(gaps) - MAX_GAPS_PER_SCHOOL))
    return "; ".join(parts)


def facilities_text(context, lang):
    i = 0 if lang == "en" else 1
    parts = []
    sanctioned, filled = context["teacher_posts_sanctioned"], context["teachers_in_position"]
    if sanctioned is not None and filled is not None and filled < sanctioned:
        parts.append(t("f_posts", lang, n=filled, m=sanctioned))
    if context["multigrade_classes"] == "yes":
        parts.append(t("f_multigrade", lang))
    for field in ("drinking_water", "girls_toilet"):
        if context[field] == "not functional":
            parts.append(t(f"f_{field}", lang))
    for field, value in context.items():
        if value is None:
            parts.append(t("f_missing", lang, field=FACILITY_NAME[field][i]))
    if not parts:
        return None
    return t("facilities", lang, date=date_text(context["as_of_date"], lang, year=True), list="; ".join(parts))


def month_note(note, lang):
    if not note:
        return None
    m = month(note["month"], lang)
    if note["status"] == "school_closed":
        return t("m_school_closed", lang, month=m, note=note_text(note["note"]))
    if note["status"] == "not_yet":
        return t("m_not_yet", lang, month=m, latest=month(note["latest"], lang))
    if note["status"] == "too_early":
        return t("m_too_early", lang, first=month(note["first"], lang), latest=month(note["latest"], lang))
    return t("m_before_data", lang, month=m, first=month(note["first"], lang), latest=month(note["latest"], lang))


def note_for(visit, lang):
    """A visit note in the reply's language (visits.csv holds English and Gujarati versions)."""
    return visit["notes_gu"] if lang == "gu" else visit["notes"]


def focus(area, lang):
    return FOCUS.get(area, area) if lang == "gu" else area


# --- one function per kind of answer --------------------------------------------------------

def _last_visit(e, lang):
    return t("days_ago", lang, d=e["last_visit"]["days_ago"]) if e["last_visit"] else t("never_visited", lang)


def _list_status(f, lang):
    """A line when fewer schools than asked need support, or none can be scored; otherwise None."""
    m = month(f["month"], lang)
    need = f["counts"]["High"] + f["counts"]["Medium"]
    if need + f["counts"]["Low"] == 0:
        return t("none_scored", lang, month=m)
    if need == 0:
        return t("none_need", lang, month=m)
    if len(f["schools"]) < f["limit"]:
        return t("only_n_need", lang, n=need, month=m)
    return None


def _missing_lines(f, lang):
    m = month(f["month"], lang)
    return [t("not_enough_line", lang, name=short(e, lang), month=m, action=render_action(e["action"], lang))
            for e in f["not_enough_data"]]


def _also_lines(f, lang, missing=True):
    """What the score alone would hide: recently visited, one weak class, missing data, not visited for long."""
    also = [t("moved_down", lang, name=short(e, lang), p=prio(e["priority"], lang), s=e["score"],
              d=e["last_visit"]["days_ago"]) for e in f["moved_down"]]
    for e in f["watch"]:
        weakest = e["weakest_class"]
        if e["action"]["code"] == "class_remedial" and weakest:
            also.append(t("watch_class", lang, name=short(e, lang), v=weakest["avg_score_pct"],
                          cls=class_name(weakest["grade"], weakest["subject"], lang)))
        else:
            also.append(t("watch_other", lang, name=short(e, lang), action=render_action(e["action"], lang)))
    if missing:
        also += _missing_lines(f, lang)
    if f["long_unvisited"]:
        longest_first = sorted(f["long_unvisited"], key=lambda e: -(e["last_visit"]["days_ago"] if e["last_visit"]
                                                                     else float("inf")))
        rows = [f"{short(e, lang)} ({t('days', lang, d=e['last_visit']['days_ago'])})" if e["last_visit"]
                else f"{short(e, lang)} ({t('never_visited', lang)})" for e in longest_first]
        also.append(t("long_unvisited", lang, n=f["rules"]["long_unvisited_days"], list=", ".join(rows)))
    return also


def _list_title(f, lang):
    using = "using_latest" if f["month"] == f.get("latest_month", f["month"]) else "using_month"
    return t("top_header", lang, using=t(using, lang, month=month(f["month"], lang)))


def top_priority_schools(f, lang):
    lines = [month_note(f.get("month_note"), lang), _list_title(f, lang), ""]
    reasons = 3 if len(f["schools"]) <= 3 else 2          # keep a long list readable on a phone
    for i, e in enumerate(f["schools"], 1):
        lines += [f"{i}. {short(e, lang)}: {t('priority', lang, p=prio(e['priority'], lang))}, "
                  f"{t('score', lang, s=e['score'])} {t('last_visit_paren', lang, when=_last_visit(e, lang))}",
                  f"   {t('why', lang)}: {reasons_text(e, lang, limit=reasons)}",
                  f"   {t('do', lang)}: {render_action(e['action'], lang)}", ""]
    status = _list_status(f, lang)
    if status:
        lines += [status, ""]
    also = _also_lines(f, lang)
    if also:
        lines += [t("also", lang)] + [f"• {line}" for line in also] + [""]
    lines.append(t("higher_score", lang))
    if f["schools"]:
        lines.append(t("ask_more", lang, q=t("q_about", lang, name=short(f["schools"][0], lang))))
    options = [option(short(e, lang), t("q_about", lang, name=short(e, lang)), e["school_id"]) for e in f["schools"]]
    return lines, options


def sentence(text):
    """'average marks 38%' -> 'Average marks 38%' for a list item (Gujarati has no capitals)."""
    return text[:1].upper() + text[1:]


def priority_cards(f, lang):
    """The same visit plan as structured cards for the chat page. Every number on a card is read from
    the facts the code computed; cards never pass through the LLM (D-013)."""
    return {
        "note": month_note(f.get("month_note"), lang),
        "title": t("cards_title", lang),
        "subtitle": t("cards_sub", lang, month=month(f["month"], lang), year=f["month"][:4]),
        "schools": [{"school_id": e["school_id"], "name": short(e, lang), "priority": e["priority"],
                     "priority_label": t(f"lbl_{e['priority']}", lang),
                     "score": e["score"], "score_scale": f.get("score_scale", 100),
                     "reasons": [sentence(r) for r in reason_parts(e, lang, limit=3)],
                     "action": render_action(e["action"], lang), "last_visit": _last_visit(e, lang)}
                    for e in f["schools"]],
        "status": _list_status(f, lang),
        # Missing data stays in view on the page; the other notes fold under "Also keep in mind" (D-034).
        "missing": _missing_lines(f, lang),
        "also_title": t("also_keep", lang),
        "also": _also_lines(f, lang, missing=False),
    }


def school_summary(f, lang):
    s, p = f["school"], f["priority"]
    m = month(p["month"], lang)
    lines = [month_note(f.get("month_note"), lang),
             t("summary_header", lang, name=short(s, lang), type=t(f"type_{s['type']}", lang), n=s["enrolment"], month=m)]
    if p["status"] == "scored":
        ind = p["indicators"]
        drop = ind["attendance_drop"]
        lines += [t("priority_line", lang, p=prio(p["priority"], lang), s=p["score"]),
                  "• " + t("attendance_line", lang, v=ind["student_attendance"]["value"], k=drop["months_compared"],
                           prev=drop["previous_avg"], t=pct(p["teacher_attendance_pct"], lang)),
                  "• " + t("learning_line", lang, v=ind["learning_level"]["value"], b=ind["below_basic"]["value"],
                           r=ind["learning_level"]["results"], e=ind["learning_level"]["expected"])]
    else:
        lines += [t("not_enough_header", lang, month=m)] + [f"• {gap_text(g, lang)}" for g in p["gaps"]]
    if p["weakest_class"]:
        w = p["weakest_class"]
        lines.append("• " + t("lowest_class", lang, cls=class_name(w["grade"], w["subject"], lang), v=w["avg_score_pct"]))
    facilities = facilities_text(p["context"], lang)
    if facilities:
        lines.append("• " + facilities)
    v = p["last_visit"]
    if v:
        lines.append("• " + t("last_visit_line", lang, date=date_text(v["date"], lang), d=v["days_ago"], note=note_for(v, lang)))
    else:
        lines.append("• " + t("last_visit_short", lang, when=t("never_visited", lang)))
    lines.append(f"{t('do', lang)}: {render_action(p['action'], lang)}")
    return lines, []


def subject_analysis(f, lang):
    s = f["school"]
    name, g = short(s, lang), f["grade"]
    status = f["status"]
    if status == "not_applicable":
        reason = f["reason"]
        if reason == "grade_not_assessed":
            return [t("na_grade_not_assessed", lang, g=g, grades=grades_text(f["assessed_grades"], lang))], []
        if reason == "grade_not_offered":
            return [t("na_grade_not_offered", lang, name=name, type=t(f"type_{s['type']}", lang), g=g,
                      grades=grades_text(s["grades"], lang))], []
        if reason == "subject_not_at_school":
            return [t("na_subject_not_at_school", lang, name=name, type=t(f"type_{s['type']}", lang),
                      instead=SUBJECTS[lang][f["taught_instead"]], subject=SUBJECTS[lang][f["subject"]])], []
        instead = f["taught_instead"]
        cls = class_name(g, instead, lang)
        question = t("q_subject", lang, cls=cls, name=name)
        return ([t("na_subject_not_taught", lang, g=g, instead=SUBJECTS[lang][instead],
                   subject=SUBJECTS[lang][f["subject"]]), t("ask_one_school", lang, q=question)],
                [option(cls, question, s["school_id"])])
    cls = class_name(g, f["subject"], lang)
    if status == "no_data":
        return [t("no_results_any_month", lang, cls=cls, name=name)], []

    latest, first = f["latest"], f["first"]
    lines = [t("subject_header", lang, name=name, cls=cls, month=month(latest["month"], lang),
               v=latest["avg_score_pct"], bb=below_basic(latest["pct_below_basic"], lang, "long"))]
    if not f["latest_is_current_month"]:
        lines.append(t("latest_is_old", lang, missing=join([month(x, lang) for x in f["missing_months"]
                                                             if x > latest["month"]], lang)))
    trend = " → ".join(f"{month(x['month'], lang)} {pct(x['avg_score_pct'], lang)}" for x in f["trend"])
    change = f["change_since_first"]
    if first["month"] != latest["month"]:
        key = "change_down" if change < 0 else "change_up" if change > 0 else "change_none"
        trend += f" ({t(key, lang, v=abs(change), m=month(first['month'], lang))})"
    lines.append("• " + t("trend", lang, list=trend))
    others = [f"{SUBJECTS[lang][o['subject']]} {pct(o['avg_score_pct'], lang)}" for o in f["other_subjects_same_grade"]]
    if others:
        lines.append("• " + t("same_class", lang, list=", ".join(others)))
    c = f["cluster_average"]
    d = c["difference"]
    cmp = "" if d is None else t("cmp_below" if d < 0 else "cmp_above" if d > 0 else "cmp_same", lang,
                                 v=latest["avg_score_pct"])
    lines.append("• " + t("cluster_avg", lang, cls=cls, v=c["avg_score_pct"], n=c["schools"], cmp=cmp))
    facilities = facilities_text(f["context"], lang)
    if facilities:
        lines.append("• " + facilities)
    if f["related_visit_notes"]:
        lines.append(t("visit_notes", lang))
        lines += [f"• {date_text(v['date'], lang)}: {note_for(v, lang)}" for v in f["related_visit_notes"][:2]]
    if f["action"]["code"] != "routine":
        lines.append(t("cause_caveat", lang))
    lines.append(f"{t('do', lang)}: {render_action(f['action'], lang)}")
    return lines, []


def class_overview(f, lang):
    g, subject = f["grade"], f["subject"]
    if f["status"] == "not_applicable":
        if f["reason"] == "grade_not_assessed":
            return [t("na_grade_not_assessed", lang, g=g, grades=grades_text(f["assessed_grades"], lang))], []
        return [t("na_subject_not_taught", lang, g=g, instead=SUBJECTS[lang][f["taught_instead"]],
                  subject=SUBJECTS[lang][subject])], []
    if g is not None and subject:
        label = class_name(g, subject, lang)
    elif subject:
        label = t("label_all_grades", lang, subject=SUBJECTS[lang][subject])
    elif g is not None:
        label = t("label_all_subjects", lang, g=g)
    else:
        label = t("label_all_classes", lang)
    m = month(f["month"], lang)
    lines = [t("class_header", lang, label=label, month=m, v=f["average_pct"], n=f["results"])]
    concern = f["below_concern"]
    lines.append(t("below_concern", lang, c=concern["count"], n=f["results"], p=concern["pct"])
                 if concern["count"] else t("lowest_only", lang))
    options = []
    for i, r in enumerate(f["lowest"], 1):
        cls = "" if (g is not None and subject) else f", {class_name(r['grade'], r['subject'], lang)}"
        lines.append(f"{i}. " + t("class_row", lang, name=short(r, lang), cls=cls, v=r["avg_score_pct"],
                                  bb=below_basic(r["pct_below_basic"], lang, "short")))
        question = t("q_subject", lang, cls=class_name(r["grade"], r["subject"], lang), name=short(r, lang))
        options.append(option(f"{short(r, lang)}{cls}", question, r["school_id"]))
    if f["no_result"]:
        lines.append(t("no_result", lang, month=m, list=", ".join(short(s, lang) for s in f["no_result"])))
    if options:
        lines.append(t("ask_one_school", lang, q=options[0]["question"]))
    return lines, options


def attendance_trend(f, lang):
    if "school" in f:
        return _attendance_school(f, lang)
    lines = [month_note(f.get("month_note"), lang), t("att_cluster_header", lang)]
    for r in f["months"]:
        m = month(r["month"], lang)
        if r["status"] == "school_closed":
            lines.append(t("att_closed", lang, month=m, note=note_text(r["note"])))
        else:
            lines.append(t("att_cluster_month", lang, month=m, v=r["student_attendance_pct"],
                           r=r["schools_reporting"], t=r["schools_total"]))
    m = month(f["month"], lang)
    if f["biggest_drops"]:
        lines.append(t("att_drops", lang, month=m))
        lines += ["• " + t("att_drop_row", lang, name=short(d, lang), prev=d["previous_avg"], s=d["student_attendance_pct"])
                  for d in f["biggest_drops"]]
    low = f["low_teacher_attendance"]
    if low["schools"]:
        rows = ", ".join(f"{short(s, lang)} {s['teacher_attendance_pct']}%" for s in low["schools"])
        lines.append(t("att_teacher_low", lang, p=low["below_pct"], list=rows))
    if f["not_reported"]:
        lines.append(t("att_not_reported", lang, month=m, list=", ".join(short(s, lang) for s in f["not_reported"])))
    return lines, [option(short(d, lang), t("q_attendance", lang, name=short(d, lang)), d["school_id"])
                   for d in f["biggest_drops"]]


def _attendance_school(f, lang):
    s = f["school"]
    name = short(s, lang)
    lines = [month_note(f.get("month_note"), lang)]
    asked = f.get("asked_month")
    if asked:
        row = next(r for r in f["months"] if r["month"] == asked)
        m = month(asked, lang)
        if row["status"] == "missing":
            lines.append(t("att_no_record", lang, name=name, month=m))
        elif row["status"] == "recorded" and row["student_attendance_pct"] is None:
            lines.append(t("att_children_missing", lang, name=name, month=m))
        elif row["status"] == "recorded":
            lines.append(t("att_asked", lang, name=name, month=m, s=pct(row["student_attendance_pct"], lang),
                           t=pct(row["teacher_attendance_pct"], lang)))
        lines.append("")
    lines.append(t("att_school_header", lang, name=name))
    for r in f["months"]:
        m = month(r["month"], lang)
        if r["status"] == "school_closed":
            lines.append(t("att_closed", lang, month=m, note=note_text(r["note"])))
        elif r["status"] == "missing":
            lines.append(t("att_missing", lang, month=m))
        else:
            lines.append(t("att_month", lang, month=m, s=pct(r["student_attendance_pct"], lang),
                           t=pct(r["teacher_attendance_pct"], lang)))
    change = f["change"]
    if change:
        m = month(f["latest_month"], lang)
        k = change["months_compared"]
        key = "att_lower" if change["change"] < 0 else "att_higher" if change["change"] > 0 else "att_same"
        now = next(r for r in f["months"] if r["month"] == f["latest_month"])["student_attendance_pct"]
        lines.append(t(key, lang, month=m, now=now, k=k, prev=change["previous_avg"]))
    c = next(r for r in f["cluster_months"] if r["month"] == f["latest_month"])
    lines.append(t("att_cluster_line", lang, month=month(c["month"], lang), v=c["student_attendance_pct"],
                   r=c["schools_reporting"], t=c["schools_total"]))
    return lines, []


def missing_data(f, lang):
    if "school" in f:
        name = short(f["school"], lang)
        if not f["gaps"]:
            return [t("gaps_school_none", lang, name=name)], []
        lines = [t("gaps_school_header", lang, name=name)] + [f"• {gap_text(g, lang)}" for g in f["gaps"]]
        lines.append(f"{t('do', lang)}: {render_action(f['action'], lang)}")
        return lines, []
    lines = [t("gaps_header", lang, date=date_text(f["as_of"], lang), n=f["schools_with_gaps"], t=f["schools_total"])]
    not_enough = {s["school_id"] for s in f["not_enough_data_this_month"]}
    if not_enough:
        lines.append(t("gaps_not_enough", lang, month=month(f["month"], lang)))
        lines += [f"• {short(s, lang)}: {gaps_text(s['gaps'], lang)}" for s in f["not_enough_data_this_month"]]
    others = sorted((s for s in f["schools"] if s["school_id"] not in not_enough),
                    key=lambda s: max(g.get("month", "") for g in s["gaps"]), reverse=True)
    if others:
        lines.append(t("gaps_other", lang))
        lines += [f"• {short(s, lang)}: {gaps_text(s['gaps'], lang)}" for s in others[:MAX_GAP_SCHOOLS]]
        if len(others) > MAX_GAP_SCHOOLS:
            lines.append(t("gaps_also", lang, list=", ".join(short(s, lang) for s in others[MAX_GAP_SCHOOLS:])))
    if f["closed_months"]:
        lines.append(t("gaps_closed", lang, months=join([month(m, lang) for m in f["closed_months"]], lang)))
    return lines, [option(short(s, lang), t("q_gaps", lang, name=short(s, lang)), s["school_id"])
                   for s in f["not_enough_data_this_month"]]


def recent_visits(f, lang):
    if "school" in f:
        name = short(f["school"], lang)
        visits = f["visits"]
        if not visits:
            return [t("visit_none", lang, name=name)], []
        v = visits[0]
        lines = [t("visit_last", lang, name=name, date=date_text(v["date"], lang), d=v["days_ago"],
                   focus=focus(v["focus_area"], lang)), t("visit_note", lang, note=note_for(v, lang))]
        if len(visits) > 1:
            lines.append(t("visit_earlier", lang, list=", ".join(
                f"{date_text(x['date'], lang)} ({focus(x['focus_area'], lang)})" for x in visits[1:])))
        return lines, []
    lines = [t("visits_30", lang, w=f["window_days"], n=f["visits_in_window"])]
    recent = sorted((r for r in f["schools"] if r["last_visit"] and r["last_visit"]["days_ago"] <= f["window_days"]),
                    key=lambda r: r["last_visit"]["days_ago"])
    if recent:                                        # "which schools did I visit this month?"
        lines.append(t("visits_recent", lang, w=f["window_days"], list=", ".join(
            f"{short(r, lang)} ({t('days_ago', lang, d=r['last_visit']['days_ago'])})" for r in recent)))
    lines.append(t("visits_longest", lang))
    for i, r in enumerate(f["schools"][:MAX_VISIT_ROWS], 1):
        v = r["last_visit"]
        row = (t("visit_row", lang, name=short(r, lang), d=v["days_ago"], date=date_text(v["date"], lang)) if v
               else t("visit_row_never", lang, name=short(r, lang)))
        lines.append(f"{i}. {row}")
    first = f["schools"][0]
    lines.append(t("ask_visit", lang, name=short(first, lang)))
    return lines, []


def list_schools(f, lang):
    """Every school in one short message: by need (with its need for help), or by type when that was asked."""
    if f.get("by") == "type":
        lines = [t("list_types_header", lang, n=f["schools_total"], p=f["types"]["primary"], u=f["types"]["upper_primary"])]
        for kind in ("primary", "upper_primary"):
            names = [short(s, lang) for s in f["schools"] if s["type"] == kind]
            lines.append("• " + t("list_group", lang, label=t(f"lbl_{kind}", lang), n=len(names), list=", ".join(names)))
    else:
        lines = [t("list_header", lang, n=f["schools_total"], month=month(f["month"], lang))]
        for p in ("High", "Medium", "Low", None):
            group = [s for s in f["schools"] if s["priority"] == p]
            if group:
                names = ", ".join(short(s, lang) if p is None else f"{short(s, lang)} {s['score']}" for s in group)
                label = t(f"lbl_{p}", lang) if p else t("lbl_waiting", lang)
                lines.append("• " + t("list_group", lang, label=label, n=len(group), list=names))
    first = f["schools"][0]
    lines.append(t("ask_one_school", lang, q=t("q_about", lang, name=short(first, lang))))
    options = [option(short(s, lang), t("q_about", lang, name=short(s, lang)), s["school_id"])
               for s in f["schools"] if s["priority"] == "High"]
    return lines, options


def officer_summary(f, lang):
    m = month(f["month"], lang)
    c = f["counts"]
    lines = [t("off_header", lang, month=m, year=f["month"][:4], t=f["schools_total"]), "",
             t("off_counts", lang, h=c["High"], m=c["Medium"], l=c["Low"], n=c["not_enough_data"])]
    high = [b for b in f["need_support"] if b["priority"] == "High"]
    medium = [b for b in f["need_support"] if b["priority"] == "Medium"]
    lines += ["• " + t("off_school", lang, name=short(b, lang), s=b["score"], reason=reasons_text(b, lang, limit=2))
              for b in high]
    if medium:
        lines.append("• " + t("off_medium", lang, list=", ".join(f"{short(b, lang)} ({b['score']})" for b in medium)))
    a = f["cluster_attendance"]
    lines += ["", t("off_attendance", lang, v=a["student_attendance_pct"], r=a["schools_reporting"], t=a["schools_total"])]
    if f["not_enough_data"]:
        lines.append(t("off_data", lang, month=m, list=join([short(b, lang) for b in f["not_enough_data"]], lang)))
    lines += ["", t("off_plan", lang, list=join([short(b, lang) for b in f["visit_plan"]], lang))]
    lines += [t("off_phone", lang, name=short(b, lang), d=b["days_since_visit"]) for b in f["phone_follow_up"]]
    watch = []
    for b in f["watch"]:
        w = b["weakest_class"]
        if b["action"]["code"] == "class_remedial" and w:
            watch.append(f"{short(b, lang)} {class_name(w['grade'], w['subject'], lang)} ({w['avg_score_pct']}%)")
        else:
            watch.append(short(b, lang))
    if watch:
        lines.append(t("off_watch", lang, list=", ".join(watch)))
    return lines, []


def help_reply(f, lang, key="help"):
    return [t(key, lang)] + [f"• {q}" for q in EXAMPLES[lang]], example_options(lang)


def boundary(key):
    def render(f, lang):
        return [t(key, lang)] + [f"• {q}" for q in EXAMPLES[lang][:3]], example_options(lang)
    return render


def school_not_found(f, lang):
    lines = [t("not_found", lang, name=f["name"])]
    if f["suggestions"]:
        lines.append(t("did_you_mean", lang, list=", ".join(short(s, lang) for s in f["suggestions"])))
        options = [option(short(s, lang), f["question"], s["school_id"]) for s in f["suggestions"]]
    else:
        lines.append(t("your_schools", lang, list=", ".join(short(s, lang) for s in f["schools"])))
        options = []
    return lines, options


def clarify_school(f, lang):
    head = t("one_at_a_time", lang) if f["reason"] == "several_named" else t("clarify_school", lang)
    lines = [head] + [f"{i}. {short(s, lang)}" for i, s in enumerate(f["candidates"], 1)] + [t("reply_with_name", lang)]
    return lines, [option(short(s, lang), f["question"], s["school_id"]) for s in f["candidates"]]


def clarify_grade(f, lang):
    s = f["school"]
    grades = f["grades"]
    lines = [t("clarify_grade", lang, name=short(s, lang), list=grades_text(grades, lang))]
    return lines, [option(class_name(g, f["subject"], lang), f"{f['question']} ({class_name(g, f['subject'], lang)})",
                          s["school_id"]) for g in grades]


def clarify_subject(f, lang):
    g = f["grade"]
    names = [SUBJECTS[lang][x] for x in f["subjects"]]
    lines = [t("clarify_subject", lang, g=g, list=", ".join(names))]
    return lines, [option(class_name(g, x, lang), f"{f['question']} ({class_name(g, x, lang)})", f["school"]["school_id"])
                   for x in f["subjects"]]


RENDER = {
    "top_priority_schools": top_priority_schools,
    "school_summary": school_summary,
    "subject_analysis": subject_analysis,
    "class_overview": class_overview,
    "attendance_trend": attendance_trend,
    "missing_data": missing_data,
    "recent_visits": recent_visits,
    "officer_summary": officer_summary,
    "list_schools": list_schools,
    "help": help_reply,
    "out_of_scope": boundary("out_of_scope"),
    "people_judgement": boundary("people_judgement"),
    "personal_info": boundary("personal_info"),
    "not_allowed": boundary("not_allowed"),
    "school_not_found": school_not_found,
    "clarify_school": clarify_school,
    "clarify_grade": clarify_grade,
    "clarify_subject": clarify_subject,
}


def render(kind, facts, lang):
    """(reply text, tap options) for one answer, in 'en' or 'gu'."""
    lines, options = RENDER[kind](facts, lang)
    text = "\n".join(line for line in lines if line is not None).strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text, options
