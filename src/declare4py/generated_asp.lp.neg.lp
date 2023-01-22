activity(driving_test).
has_attribute(driving_test, driver).
has_attribute(driving_test, grade).
activity(getting_license).
has_attribute(getting_license, driver).
has_attribute(getting_license, grade).
activity(resit).
has_attribute(resit, driver).
has_attribute(resit, grade).
activity(test_failed).
has_attribute(test_failed, driver).

value(driver, fabrizio).
value(driver, mike).
value(driver, marlon).
value(driver, raimundas).
value(grade, 1..5).

template(0,"Response").
activation(0,driving_test).
target(0,getting_license).
activation_condition(0,T) :- time(T).
correlation_condition(0,T):- correlation_condition_1(0,T).
correlation_condition_1(0,T) :- assigned_value(Grade,V,T),V>2.


template(1,"Response").
activation(1,driving_test).
target(1,resit).
activation_condition(1,T):- activation_condition_1(1,T).
activation_condition_1(1,T) :- assigned_value(Grade,V,T),V<=2.
correlation_condition(1,T):- time(T).


template(2,"Response").
activation(2,driving_test).
target(2,test_failed).
activation_condition(2,T):- activation_condition_1(2,T).
activation_condition_1(2,T) :- assigned_value(Grade,V,T),V<=2.
correlation_condition(2,T):- time(T).



sat(0).
sat(2).
:-sat(1).
:- #count{T:trace(A,T), activation_condition(1,T)} < 3.