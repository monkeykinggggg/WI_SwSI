import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd

    return mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Wczytanie i spłaszczenie danych oraz Ekstrakcja cech
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Notatki
    Dota 2 do gra w której grają dwie drużyny (5 na 5): Dire oraz Radiant.
    Celem jest zniszczyć baze przeciwnika, ale żeby to zrobić, najpierw trzeba zniszczyć wieże z odpowiednich poziomów 1,2,3.
    Wszystkie informacje sa tutaj: https://docs.opendota.com/#tag/benchmarks/operation/get_benchmarks
    """)
    return


@app.cell
def _():
    import json
    with open('./project_files/project1/competition_train.json') as file:
        json_data = json.load(file)
    return json, json_data


@app.cell
def _(json_data):
    json_data[0]['players'][0].keys()
    return


@app.cell
def _(json_data):
    import random
    json_data[random.randrange(100)]
    return (random,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Przydatne pola:
    - radiant_score - ilość zapitych przez drużynę Radiant na koniec meczu
    - dire_score - analogicznie przez drugą drużynę
    - game_mode - rodzaje modułów gry: https://github.com/odota/dotaconstants/blob/master/json/game_mode.json
    - first_blood_time - w sekundach
    - duration
    - tower_status_radiant
    - tower_status_dire
    - barracks_status_radiant
    - barracks_status_dire

    Nieprzydatne ale, żeby zrozumieć:
    leagueid - liga zawodów ( moga być miedzynarodowe, krajowe, regionalne itd.), w każdej lidze grają zawodnicy różnych tierach
    """)
    return


@app.cell
def _():
    match_useful_columns = ["match_id", "tier",
                            "radiant_score", "dire_score",
                            "game_mode","first_blood_time","duration",  
                            "tower_status_radiant","tower_status_dire","barracks_status_radiant","barracks_status_dire",
                            ]
    return (match_useful_columns,)


@app.cell
def _(json_data, random):
    json_data[random.randrange(100)]['players'][0]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Przydatne pola o graczu:
    - `gold_per_min` - ilość złota zarabianego/min meczu
    - `xp_per_min`- tu o doświadczeniu
    - `kills`  - ile zabił
    - `deaths` - ile razy gracz zginął ( można się odradzać)
    - `assists` - w ilu zabójstwach gracz pomagał
    - `last_hits` - ile gracz usunął obiektów z pośród ostatnich możliwych
    - `hero_damage` - całkowite szkody jakie gracz zadał innym  , `net_worth`,
    - `level` - obecny poziom postaci w grze ( w trakcie gry, gracz zdobywa następne levele)
    - `kda` - ogólna wydajność: `(kills + assists) / deaths`
    - `net_worth` - ostateczny zgromadzony majątek gracza na koniec meczu

    isRadiant - ważna cecha do późniejszek analizy różnic
    """)
    return


@app.cell
def _():
    players_useful_columns = ['gold_per_min', 'xp_per_min', 'kills', 'deaths', 'assists','last_hits', 'hero_damage', 'net_worth', 'kda',
                              'level', 
                              'isRadiant'
                             ]
    return (players_useful_columns,)


@app.cell
def _(json_data, match_useful_columns, pd, players_useful_columns):
    def load_players(match_columns_to_retrieve,players_columns_to_retrieve, json_file=json_data):
        players = []
        for match in json_file:
            for p in match['players']:
                row = {}
                for col in players_columns_to_retrieve:
                    row[col] = p.get(col)

                for col in match_columns_to_retrieve:
                    row[col] = match.get(col)

                row['match_id'] = match.get('match_id')
                players.append(row)
        return players

    players_df = pd.DataFrame(load_players(match_useful_columns, players_useful_columns))
    return load_players, players_df


@app.cell
def _(players_df):
    players_df.head()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Weryfikacja
    """)
    return


@app.cell
def _(match_useful_columns, players_df, players_useful_columns):
    len(match_useful_columns)+len(players_useful_columns)+1 == players_df.shape[1]
    return


@app.cell
def _(json_data, players_df):
    len(json_data)*10 == players_df.shape[0]
    return


@app.cell
def _(match_useful_columns, pd, players_useful_columns):
    numeric_cols_for_mean_calculations = players_useful_columns[:-1]

    def aggregate_team(df_team, team_name, cols_for_calculations = numeric_cols_for_mean_calculations):
        aggregation = {}
        for col in cols_for_calculations:
            if col in df_team.columns:
                aggregation[f"{team_name}_{col}_mean"] = df_team[col].mean()
        return aggregation

    def concatenate_for_final_dataframe(df_players, match_columns = match_useful_columns):
        radiant_df = df_players[df_players['isRadiant'] == True]
        dire_df = df_players[df_players['isRadiant'] == False]

        radiant_team_stats = aggregate_team(radiant_df, "radiant")
        dire_team_stats = aggregate_team(dire_df, "dire")
        teams_ratios = {}

        for radiant_key, radiant_val in radiant_team_stats.items():
            base_key = radiant_key.replace("radiant_", "")
            dire_key = radiant_key.replace("radiant_", "dire_")
            teams_ratios[f"{base_key}_ratio"] = radiant_val - dire_team_stats[dire_key]

        match_data = df_players.iloc[0][match_columns].to_dict()
        aggregated_row_for_match = { **match_data, **radiant_team_stats, **dire_team_stats, **teams_ratios}
        return pd.DataFrame([aggregated_row_for_match])

    return (concatenate_for_final_dataframe,)


@app.cell
def _(concatenate_for_final_dataframe, pd, players_df):
    rows = []
    for match_id, df_match in players_df.groupby('match_id'):
        rows.append(concatenate_for_final_dataframe(df_match))

    temp_df = pd.concat(rows, ignore_index=True)
    return (temp_df,)


@app.cell
def _(temp_df):
    def get_match_data_ratios(df):
        df[f"score_ratio"] = df['radiant_score']-df['dire_score']
        df["tower_status_ratio"] = df['tower_status_radiant'] - df['tower_status_dire']
        df['barracks_status_ratio'] = df['barracks_status_radiant']-df['barracks_status_dire']
        return df
    final_df = get_match_data_ratios(temp_df)
    return final_df, get_match_data_ratios


@app.cell
def _(final_df):
    final_df
    return


@app.cell
def _(final_df):
    final_df.columns
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Eksploracja i wizualizacja
    """)
    return


@app.cell
def _(final_df, pd):
    tier_order = ['Herald', 'Guardian', 'Crusader', 'Archon','Legend', 'Ancient', 'Divine', 'Immortal']
    final_df['tier'] = pd.Categorical(final_df['tier'], categories=tier_order, ordered=True)
    final_df['tier']
    return (tier_order,)


@app.cell
def _(final_df):
    import matplotlib.pyplot as plt
    import seaborn as sns

    features = list(final_df.columns[2:])
    def run_distributions():
        fig, axes = plt.subplots(nrows=20, ncols=3, figsize=(30, 60))
        axes = axes.flatten()

        for i, feature in enumerate(features):
            sns.kdeplot(data=final_df, x=feature, hue='tier', fill=True, ax=axes[i])
            axes[i].set_title(f'Gęstość rozkładu {feature}')
            axes[i].set_xlabel('')
            axes[i].set_ylabel('')

        for j in range(len(features), len(axes)):
            fig.delaxes(axes[j])
        plt.tight_layout()
        plt.show()

    run_distributions()
    return features, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Cecha `game_mode` oraz `gold_per_min_mean_ratio` zostaną usunięte ze zbioru cech. Na wykresie gęstości wartości tych cech nie zauważamy zróżnicowania względem tieru. Wręcz przeciwnie, dla każdego tieru jest to rozkład o malutkim rozproszeniu. Najwyraźniej nie ma różnicy pomiędzy graczami z różnych rang pod względem ilości pozyskiwanego złota na minutę. Dla analogicznej cechy `dire_gold_per_min_mean_ratio` już widzimy zróżnicowanie pomiędzy tierami na wykresie.

    Zaskakuje rozkład cechy `barracks_status_ratio`. Można zauważyć, że im gra niższego tieru, tym ilość zniszczonych baraków przez obie drużyny jest porównywalna. Ta cecha ma wyróżniający się wykres w porównaniu do pozostałych przez to.
    """)
    return


@app.cell
def _(features, final_df, plt, sns, tier_order):
    def run_boxplot(to=tier_order):
        fig, axes = plt.subplots(nrows=20, ncols=3, figsize=(30, 60))
        axes = axes.flatten()

        for i, feature in enumerate(features):
            sns.boxplot(x='tier', y=feature, data=final_df, order=to, ax=axes[i])
            axes[i].set_title(f'Rozkład {feature} w podziale na tiery')
            axes[i].set_ylabel(feature)
            axes[i].set_xlabel('Tier')
        for j in range(len(features), len(axes)):
            fig.delaxes(axes[j])
        plt.tight_layout()
        plt.show()

    run_boxplot()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Usuwam również cechę `kda_mean_ratio` oraz jej odpowiedniki dla obu drużyn, ponieważ jest ona liniowo zależna od pozostałych cech, jako, że jest wyliczana z innych kolumn jak: `deaths`, `assists` itd.
    """)
    return


@app.cell
def _():
    final_features = [
        'first_blood_time', 'duration',
        'score_ratio', 'tower_status_ratio', 'barracks_status_ratio',

        'xp_per_min_mean_ratio','kills_mean_ratio', 
        'deaths_mean_ratio', 'assists_mean_ratio',
        'last_hits_mean_ratio', 'hero_damage_mean_ratio',
        'net_worth_mean_ratio', 'level_mean_ratio',


        'radiant_gold_per_min_mean',
        'radiant_xp_per_min_mean', 'radiant_kills_mean',
        'radiant_deaths_mean', 'radiant_assists_mean',
        'radiant_last_hits_mean', 'radiant_hero_damage_mean',
        'radiant_net_worth_mean', 'radiant_level_mean',

        'dire_gold_per_min_mean',
        'dire_xp_per_min_mean', 'dire_kills_mean',
        'dire_deaths_mean', 'dire_assists_mean',
        'dire_last_hits_mean', 'dire_hero_damage_mean',
        'dire_net_worth_mean', 'dire_level_mean',

    ]
    len(final_features)
    return (final_features,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Ostatecznie pozostawiam 13 cech finalnych do uczenia
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Model — Klasyfikacja tieru
    """)
    return


@app.cell
def _(final_df, final_features):
    int(final_df[final_features + ['tier']].isna().sum().sum())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nie ma brakujących wartości.
    """)
    return


@app.cell
def _(final_df, final_features):
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

    X = final_df[final_features]
    y = final_df['tier']
    X_train, X_val, y_train, y_val = train_test_split(X,y, test_size=0.1, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    return (
        LogisticRegression,
        X_train_scaled,
        X_val_scaled,
        accuracy_score,
        classification_report,
        confusion_matrix,
        scaler,
        y_train,
        y_val,
    )


@app.cell
def _(LogisticRegression, X_train_scaled, X_val_scaled, y_train, y_val):
    y_train_encoded = y_train.cat.codes
    y_val_encoded = y_val.cat.codes
    model = LogisticRegression(max_iter=500, random_state=42)
    model.fit(X_train_scaled, y_train_encoded)
    y_pred = model.predict(X_val_scaled)
    return model, y_pred, y_train_encoded, y_val_encoded


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Wyniki Modelu Logistycznego
    """)
    return


@app.cell
def _(
    accuracy_score,
    classification_report,
    confusion_matrix,
    tier_order,
    y_pred,
    y_val_encoded,
):
    print(f"Accuracy: {accuracy_score(y_val_encoded, y_pred):.6f}\n")

    print("Raport Klasyfikacji:")
    print(classification_report(y_val_encoded, y_pred, target_names=tier_order))

    print("Macierz Pomyłek:")
    conf_matrix = confusion_matrix(y_val_encoded, y_pred)
    print(conf_matrix)
    return


@app.cell
def _(X_train_scaled, X_val_scaled, np, y_train_encoded):
    import statsmodels.api as sm
    X_train_sm = sm.add_constant(X_train_scaled)
    X_val_sm = sm.add_constant(X_val_scaled)
    glm_model = sm.OLS(y_train_encoded, X_train_sm)
    glm_fit = glm_model.fit()


    y_pred_glm_prob = glm_fit.predict(X_val_sm)
    y_pred_glm = np.clip(np.round(y_pred_glm_prob), 0, 7).astype(int)
    return glm_fit, y_pred_glm


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Wyniki Modelu GLM
    """)
    return


@app.cell
def _(
    accuracy_score,
    classification_report,
    confusion_matrix,
    tier_order,
    y_pred_glm,
    y_val_encoded,
):
    print(f"Accuracy: {accuracy_score(y_val_encoded, y_pred_glm):.6f}\n")

    print("Raport Klasyfikacji:")
    print(classification_report(y_val_encoded, y_pred_glm, target_names=tier_order))

    print("Macierz Pomyłek:")
    conf_matrix_glm = confusion_matrix(y_val_encoded, y_pred_glm)
    print(conf_matrix_glm)
    return


@app.cell
def _(glm_fit):
    print(glm_fit.summary())
    return


@app.cell
def _(X_train_scaled, X_val_scaled, y_train_encoded):
    import xgboost as xgb

    xgb_model = xgb.XGBClassifier(
        num_class=8,                
        random_state=42,
        learning_rate=0.1
    )
    xgb_model.fit(X_train_scaled, y_train_encoded)
    y_pred_xgb = xgb_model.predict(X_val_scaled)
    return (y_pred_xgb,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Wyniki Modelu XGBoost
    """)
    return


@app.cell
def _(
    accuracy_score,
    classification_report,
    confusion_matrix,
    tier_order,
    y_pred_xgb,
    y_val_encoded,
):
    print(f"Accuracy: {accuracy_score(y_val_encoded, y_pred_xgb):.6f}\n")
    print("Raport Klasyfikacji:")
    print(classification_report(y_val_encoded, y_pred_xgb, target_names=tier_order))

    print("Macierz Pomyłek:")
    print(confusion_matrix(y_val_encoded, y_pred_xgb))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Parametry wykorzystane w trenowaniu danych
    #### Podział na dane treningowe i walidacyjne:
    - `test_size=0.1` - taki podział zwracał najlepsze wyniki Accuracy ( w stosunku do 0.2 czy 0.3 to była różnica nawet 3 pkt procentowych)
    - `stratify=y` - równomierność ilości klas mocno polepszała wyniki Accuracy
    #### Regresja logistyczna:
    - `max_iter = 500` - większa ilość iteracji nie poprawiała wyniku
    #### XGBoost:
    - `learning_rate=0.1` - najlepszy wynik, przetestowano wartości 0.1-0.9

    ### Porównanie modeli
    Regresja logistyczna najlepiej radzi sb z danymi jeżeli chodzi o metrykę Accuracy, natomiast macierz pomyłek na najbardziej diagonalną wygląda przy użyciu modelu XGboost, mimo, że accuracy jest niższe.

    ### Wnioski na temat cech
    Na podstawie podsumowania w modelu GLM można zauważyć, że cecha `barracks_status_ratio` ( x5 ) jednak nie wyróżnia się tak jak przewidywano. W tej samej tabelce widzimy, że cecha `duration`(x2) bardzo się wyróżnia, mając wartość współczynnika trzykrotnie większą od następnych największych wartości absolutnych wag dla modelu. Zatem długość trwania rozgrywki jest cechą która najmocniej rozróżnia graczy grających na różnych tierach. Rzeczywiście, gdy zobaczymy na wykresy np. pudełkowy wykres, zaobserwujemy, że długość meczu wzrasta w meczach dla najbardziej i najmniej doświadczonych zawodników (największa i najmniejsza liga), przy czym dla najniższego tieru `duration` ma bardzo duży zakres wartości, przez co długość meczu jest mniej przewidywalna niż dla najwyższego tieru ( tu widzimy 'idealnego' gaussa)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Predykcja i submission
    """)
    return


@app.cell
def _(json, load_players, match_useful_columns, pd, players_useful_columns):
    with open('./project_files/project1/competition_test.json') as f:
        test_json = json.load(f)
    match_useful_columns.remove('tier')
    test_players_df = pd.DataFrame(load_players(match_useful_columns, players_useful_columns, json_file = test_json ))
    return (test_players_df,)


@app.cell
def _(
    concatenate_for_final_dataframe,
    get_match_data_ratios,
    pd,
    test_players_df,
):
    test_rows = []
    for match_test_id, df_test_match in test_players_df.groupby('match_id'):
        test_rows.append(concatenate_for_final_dataframe(df_test_match))

    temp_test_df = pd.concat(test_rows, ignore_index=True)
    final_test_df = get_match_data_ratios(temp_test_df)
    final_test_df.shape
    return (final_test_df,)


@app.cell
def _(final_features, final_test_df):
    int(final_test_df[final_features].isna().sum().sum())
    return


@app.cell
def _(final_features, final_test_df, model, scaler):
    X_test = final_test_df[final_features]
    X_test_scaled = scaler.transform(X_test)
    y_test_output = model.predict(X_test_scaled)
    final_test_df.describe()
    return (y_test_output,)


@app.cell
def _(final_df, y_test_output):
    oryginalne_kategorie = final_df['tier'].cat.categories
    predicted_tier_names = [oryginalne_kategorie[i] for i in y_test_output]
    return (predicted_tier_names,)


@app.cell
def _(predicted_tier_names):
    predicted_tier_names
    return


@app.cell
def _(final_test_df, pd, predicted_tier_names):
    submission = pd.DataFrame({
        'id': final_test_df['match_id'].values,
        'tier': predicted_tier_names
    })
    submission.head()
    return (submission,)


@app.cell
def _(submission):
    print(f"\nLiczba meczów: {len(submission)}")
    print(f"\nRozkład predykcji:")
    print(submission['tier'].value_counts())
    return


@app.cell
def _(submission):
    submission.to_csv('./project_files/project1/submission.csv', index=False)
    print("Zapisano")
    return


if __name__ == "__main__":
    app.run()
