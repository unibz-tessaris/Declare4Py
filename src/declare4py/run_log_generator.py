from __future__ import annotations

from boolean import boolean
import logging
from src.declare4py.log_utils.log_analyzer import LogAnalyzer
from src.declare4py.log_utils.parsers.declare.declare_parsers import DeclareParser
from src.declare4py.models.log_generation.asp.asp_generator import AspGenerator

logging.basicConfig(level=logging.INFO)



decl = """
activity Driving_Test
bind Driving_Test: Driver, Grade
activity Getting_License
bind Getting_License: Driver
activity Resit
bind Resit: Driver, Grade
activity Test_Failed
bind Test_Failed: Driver
Driver: Fabrizio, Mike, Marlon, Raimundas
Grade: integer between 1 and 5
# Response[Driving_Test, Getting_License] |A.Grade>2 | |
Response[Driving_Test, Getting_License] | |T.Grade>2 |
Response[Driving_Test, Resit] |A.Grade<=2 | |
Response[Driving_Test, Test_Failed] |A.Grade<=2 | |
"""


decl = """activity ER Triage
bind ER Triage: org_group, Diagnose, Age
activity ER Registration
bind ER Registration: InfectionSuspected, org_group, DiagnosticBlood, DisfuncOrg, SIRSCritTachypnea, Hypotensie, SIRSCritHeartRate, Infusion, DiagnosticArtAstrup, Age, DiagnosticIC, DiagnosticSputum, DiagnosticLiquor, DiagnosticOther, SIRSCriteria2OrMore, DiagnosticXthorax, SIRSCritTemperature, DiagnosticUrinaryCulture, SIRSCritLeucos, Oligurie, DiagnosticLacticAcid, Diagnose, Hypoxie, DiagnosticUrinarySediment, DiagnosticECG
activity ER Sepsis Triage
bind ER Sepsis Triage: org_group, Diagnose, Age
activity Leucocytes
bind Leucocytes: Leucocytes, org_group, Diagnose, Age
activity CRP
bind CRP: CRP, org_group, Diagnose, Age
activity LacticAcid
bind LacticAcid: org_group, LacticAcid
activity IV Antibiotics
bind IV Antibiotics: org_group
activity Admission NC
bind Admission NC: org_group
activity IV Liquid
bind IV Liquid: org_group, Diagnose, Age
activity Release A
bind Release A: org_group
activity Return ER
bind Return ER: org_group
activity Admission IC
bind Admission IC: org_group
CRP: float between 5.0 and 573.0
InfectionSuspected: true, false
org_group: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, ?
DiagnosticBlood: true, false
DisfuncOrg: true, false
SIRSCritTachypnea: true, false
Hypotensie: true, false
SIRSCritHeartRate: true, false
Infusion: true, false
Leucocytes: float between 0.2 and 381.3
DiagnosticArtAstrup: true, false
LacticAcid: float between 0.2 and 14.9
Age: integer between 20 and 90
DiagnosticIC: true, false
DiagnosticSputum: false, true
DiagnosticLiquor: false, true
DiagnosticOther: false, true
SIRSCriteria2OrMore: true, false
DiagnosticXthorax: true, false
SIRSCritTemperature: true, false
DiagnosticUrinaryCulture: true, false
SIRSCritLeucos: false, true
Oligurie: false, true
DiagnosticLacticAcid: true, false
Diagnose: YA, YB, YC, YD, QA, QB, QC, QD, QE, IA, IB, IC, ID, IE, AA, AB, AC, AD, AE, ZA, ZB, ZC, ZD, RA, RB, RC, RD, JA, JB, JC, JD, JE, BA, BB, A, BC, B, BD, C, BE, D, E, F, G, H, I, J, K, L, M, N, SA, O, SB, P, SC, Q, SD, R, S, T, U, V, KA, W, KB, X, KC, Y, KD, Z, KE, CA, CB, CC, CD, CE, TA, TB, TC, TD, LA, LB, LC, LD, LE, DA, DB, DC, DD, DE, UA, UB, UC, UD, MA, MB, MC, MD, ME, EA, EB, EC, ED, EE, VA, VB, VC, VD, NA, NB, NC, ND, FA, FB, FC, FD, FE, WA, WB, WC, WD, OA, OB, OC, OD, OE, GA, GB, GC, GD, GE, XA, XB, XC, XD, PA, PB, PC, PD, PE, HA, HB, HC, HD, HE
Hypoxie: false, true
DiagnosticUrinarySediment: true, false
DiagnosticECG: true, false
Chain Response[Admission NC, Release B] | A.org_group is K |T.org_group is E |
Chain Response[Admission NC, Release A] | A.org_group is I |T.org_group is E | 133020,957701,s
Chain Precedence[IV Liquid, Admission NC] | A.org_group is I |T.org_group is A | 92,14473,s
#Chain Response[ER Registration, ER Triage] | (A.DiagnosticArtAstrup is false) AND (A.SIRSCritHeartRate is true) AND (A.org_group is A) AND (A.DiagnosticBlood is true) AND (A.DisfuncOrg is false) AND (A.DiagnosticECG is true) AND (A.Age >= 45) AND (A.InfectionSuspected is true) AND (A.DiagnosticLacticAcid is true) AND (A.DiagnosticSputum is true) AND (A.Hypoxie is false) AND (A.DiagnosticUrinaryCulture is true) AND (A.DiagnosticLiquor is false) AND (A.SIRSCritTemperature is true) AND (A.Infusion is true) AND (A.Hypotensie is false) AND (A.DiagnosticUrinarySediment is true) AND (A.Oligurie is false) AND (A.Age <= 80) AND (A.SIRSCritTachypnea is true) AND (A.DiagnosticOther is false) AND (A.SIRSCritLeucos is false) AND (A.DiagnosticIC is true) AND (A.SIRSCriteria2OrMore is true) AND (A.DiagnosticXthorax is true) | T.org_group is C |52,2154,s
Chain Response[ER Registration, ER Triage] | (A.DiagnosticArtAstrup is false) AND (A.SIRSCritHeartRate is true) AND (A.org_group is A) AND (A.DiagnosticBlood is true) | T.org_group is C |52,2154,s
Chain Precedence[Release A, Return ER] |A.org_group is ? |T.org_group is E | 1121801,1121801,s
Chain Precedence[ER Sepsis Triage, IV Antibiotics] | A.org_group is L | T.org_group is L | 15,11000,s
Chain Response[ER Sepsis Triage, IV Antibiotics] | A.org_group is L | T.org_group is L | 15,11000,s
Chain Precedence[Admission IC, Admission NC] | A.org_group is J | T.org_group is J |
Chain Precedence[IV Antibiotics, Admission NC] | A.org_group is F | T.org_group is A | 92,14459,s
Chain Precedence[Admission NC, Release B] | A.org_group is E | T.org_group is K | 48225,48225,s
Chain Response[Admission IC, Admission NC] | A.org_group is J | T.org_group is J | 61534,61534,s
Chain Response[LacticAcid, Leucocytes] | A.LacticAcid <= 0.8 | T.Leucocytes >= 13.8 | 0,2778,m
Chain Precedence[ER Registration, ER Triage] | A.org_group is C |(T.InfectionSuspected is true) AND (T.SIRSCritTemperature is true) AND (T.DiagnosticLacticAcid is true) AND (T.DiagnosticBlood is true) AND (T.DiagnosticIC is true) AND (T.SIRSCriteria2OrMore is true) AND (T.DiagnosticECG is true) |52,2154,s"""

dp = DeclareParser()
model = dp.parse_from_string(decl)
# print(d.parsed_model)
num_of_traces = 4
num_min_events = 2
num_max_events = 4
asp = AspGenerator(
    model, num_of_traces, num_min_events,
    num_max_events, distributor_type="gaussian",
    loc=3, scale=0.8, encode_decl_model=True
)

asp.run()
# asp.to_xes("../../generated_xes.xes")


# TODO: ask how to implement TIME CONDITION in asp
# TODO: Ask Chiarello whether the generated output of lp is correct


