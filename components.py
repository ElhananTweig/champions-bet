# components.py
import streamlit as st
from datetime import datetime
import pytz
from sheets import (
    get_match_bets,
    get_available_balance,
    get_group_members,
    place_bet,
    update_bet,
    cancel_bet
)

ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")



# ────────────────────────────────────────────────────────────────────────────────
# פונקציית רינדור משחקים (מוגדרת כאן כי היא משתמשת ב-session state)
# ────────────────────────────────────────────────────────────────────────────────
def _render_matches(matches, user_bets_df, username, group_id, is_admin, editable):
    for _, match in matches.iterrows():
        match_id = match["match_id"]
        now = datetime.now(ISRAEL_TZ)

        # הימור קיים של המשתמש על המשחק הזה
        existing_bet = None
        if not user_bets_df.empty:
            eb = user_bets_df[user_bets_df["match_id"] == match_id]
            if not eb.empty:
                existing_bet = eb.iloc[0]

        with st.expander(
            f"{'🟢' if editable else '🔴'} {match['team_a']} vs {match['team_b']} — {match['stage']}",
            expanded=editable
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric(match["team_a"], f"×{match['odds_a']}")
            col2.metric("תיקו", f"×{match['odds_draw']}")
            col3.metric(match["team_b"], f"×{match['odds_b']}")

            try:
                match_time = datetime.fromisoformat(str(match["match_datetime"]))
                if match_time.tzinfo is None:
                    match_time = ISRAEL_TZ.localize(match_time)
                st.caption(f"⏱ {match_time.strftime('%d/%m/%Y %H:%M')}")
            except Exception:
                pass

            # הימורים של כולם (רק אחרי סגירה)
            if match["status"] in ("closed", "finished"):
                all_bets = get_match_bets(match_id, group_id)
                if not all_bets.empty:
                    st.markdown("**הימורי הקבוצה:**")
                    group_bets_html = '<div class="cb-group-bets">'
                    for _, b in all_bets.iterrows():
                        label = {"a": match["team_a"], "draw": "תיקו", "b": match["team_b"]}.get(b["choice"], b["choice"])
                        if b["result"] == "win":
                            result_tag_html = f'<span class="cb-group-bet-result win">+&#8362;{float(b["payout"]):.0f}</span>'
                        elif b["result"] == "loss":
                            result_tag_html = '<span class="cb-group-bet-result loss">&#10060;</span>'
                        else:
                            result_tag_html = ""
                        group_bets_html += f"""<div class="cb-group-bet">
                            <span class="cb-group-bet-user">{b['username']}</span>
                            <span class="cb-group-bet-choice">{label}</span>
                            <span class="cb-group-bet-amount">&#8362;{float(b['amount']):.0f}</span>
                            {result_tag_html}
                        </div>"""
                    group_bets_html += '</div>'
                    st.markdown(group_bets_html, unsafe_allow_html=True)

            # טופס הימור / עריכה
            if editable:
                st.markdown("---")
                available = get_available_balance(username, group_id)

                if existing_bet is not None:
                    # עריכת הימור קיים
                    current_choice = existing_bet["choice"]
                    current_amount = float(existing_bet["amount"])
                    choices = {'a': match['team_a'], 'draw': 'תיקו', 'b': match['team_b']}
                    st.markdown(f"**ההימור שלך:** {choices[current_choice]} — ₪{current_amount:.0f}")

                    choice_options = [match["team_a"], "תיקו", match["team_b"]]
                    choice_keys = ["a", "draw", "b"]
                    default_idx = choice_keys.index(current_choice)

                    new_choice_label = st.radio(
                        "שנה בחירה", choice_options,
                        index=default_idx,
                        horizontal=True,
                        key=f"choice_{match_id}"
                    )
                    new_choice = choice_keys[choice_options.index(new_choice_label)]
                    new_amount = st.number_input(
                        "סכום", min_value=1,
                        max_value=int(available + current_amount),
                        value=int(current_amount),
                        key=f"amount_{match_id}"
                    )

                    c1, c2 = st.columns(2)
                    if c1.button("💾 עדכן הימור", key=f"update_{match_id}"):
                        ok, msg = update_bet(username, group_id, match_id, new_choice, new_amount)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.cache_data.clear()
                            st.rerun()

                    if c2.button("🗑️ בטל הימור", key=f"cancel_{match_id}"):
                        ok, msg = cancel_bet(username, group_id, match_id)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.cache_data.clear()
                            st.rerun()

                else:
                    # הימור חדש
                    st.markdown(f"""<div style="font-family:'Heebo',sans-serif;font-size:0.9rem;color:#94a3b8;margin-bottom:8px;">
                        &#128176; זמין להימור: <b style="color:#22c55e;font-size:1.05rem;">&#8362;{available:.0f}</b>
                    </div>""", unsafe_allow_html=True)
                    if available <= 0:
                        st.warning("אין לך כסף זמין להימור")
                    else:
                        choice_options = [match["team_a"], "תיקו", match["team_b"]]
                        choice_keys = ["a", "draw", "b"]
                        chosen_label = st.radio(
                            "על מה מהמרים?", choice_options,
                            horizontal=True,
                            key=f"new_choice_{match_id}"
                        )
                        chosen_key = choice_keys[choice_options.index(chosen_label)]
                        amount = st.number_input(
                            "סכום הימור", min_value=1,
                            max_value=int(available),
                            value=min(100, int(available)),
                            key=f"new_amount_{match_id}"
                        )
                        if st.button("🎲 שלח הימור", key=f"bet_{match_id}"):
                            ok, msg = place_bet(username, group_id, match_id, chosen_key, amount)
                            (st.success if ok else st.error)(msg)
                            if ok:
                                st.cache_data.clear()
                                st.rerun()

                # אדמין יכול להמר בשם אחר
                if is_admin:
                    with st.expander("🔑 הימור בשם שחקן אחר"):
                        members_df = get_group_members(group_id)
                        other_members = members_df[members_df["username"] != username]["username"].tolist()
                        if other_members:
                            target_user = st.selectbox("שחקן", other_members, key=f"admin_target_{match_id}")
                            t_available = get_available_balance(target_user, group_id)
                            st.caption(f"יתרה זמינה של {target_user}: ₪{t_available:.0f}")

                            t_choice_label = st.radio(
                                "בחירה", choice_options,
                                horizontal=True,
                                key=f"admin_choice_{match_id}"
                            )
                            t_choice = choice_keys[choice_options.index(t_choice_label)]
                            t_amount = st.number_input(
                                "סכום", min_value=1,
                                max_value=max(1, int(t_available)),
                                key=f"admin_amount_{match_id}"
                            )
                            if st.button("🎲 שלח בשמו", key=f"admin_bet_{match_id}"):
                                ok, msg = place_bet(target_user, group_id, match_id, t_choice, t_amount)
                                (st.success if ok else st.error)(msg)
                                if ok:
                                    st.cache_data.clear()
                                    st.rerun()