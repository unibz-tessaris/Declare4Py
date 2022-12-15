activity(act1).
activity(act2).
activity(act3).
activity(act4).



template(0,"Existence").
activation(0,act1).
activation_condition(0,T) :- time(T).


template(1,"Existence").
activation(1,act2).
activation_condition(1,T) :- time(T).


template(2,"Existence").
activation(2,act3).
activation_condition(2,T) :- time(T).


template(3,"Existence").
activation(3,act4).
activation_condition(3,T) :- time(T).



sat(0).
sat(1).
sat(2).
sat(3).