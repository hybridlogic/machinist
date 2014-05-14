
from twisted.python.components import proxyForInterface
from twisted.internet.defer import succeed

from eliot import Field, ActionType

from ._interface import IFiniteStateMachine

def system(suffix):
    return u":".join((u"fsm", suffix))


FSM_IDENTIFIER = Field.forTypes(
    u"fsm_identifier", [unicode],
    u"An unique identifier for the FSM to which the event pertains.")
FSM_STATE = Field.forTypes(
    u"fsm_state", [unicode], u"The state of the FSM prior to the transition.")
FSM_RICH_INPUT = Field.forTypes(
    u"fsm_rich_input", [unicode],
    u"The string representation of the rich input delivered to the FSM.")
FSM_INPUT = Field.forTypes(
    u"fsm_input", [unicode],
    u"The string representation of the input symbol delivered to the FSM.")
FSM_NEXT_STATE = Field.forTypes(
    u"fsm_next_state", [unicode],
    u"The string representation of the state of the FSM after the transition.")
FSM_OUTPUT = Field.forTypes(
    u"fsm_output", [list], # of unicode
    u"A list of the string representations of the outputs produced by the "
    u"transition.")
FSM_TERMINAL_STATE = Field.forTypes(
    u"fsm_terminal_state", [unicode],
    u"The string representation of the terminal state entered by the the FSM.")

LOG_FSM_INITIALIZE = ActionType(
    system(u"initialize"),
    [FSM_IDENTIFIER, FSM_STATE],
    [FSM_TERMINAL_STATE],
    [],
    u"A finite state machine was initialized.")

LOG_FSM_TRANSITION = ActionType(
    system(u"transition"),
    [FSM_IDENTIFIER, FSM_STATE, FSM_RICH_INPUT, FSM_INPUT],
    [FSM_NEXT_STATE, FSM_OUTPUT],
    [],
    u"A finite state machine received an input made a transition.")



class FiniteStateLogger(proxyForInterface(IFiniteStateMachine, "_fsm")):
    """
    L{FiniteStateLogger} wraps another L{IFiniteStateMachine} provider and
    adds to it logging of all state transitions.
    """
    def __init__(self, fsm, logger, identifier):
        super(FiniteStateLogger, self).__init__(fsm)
        self.logger = logger
        self.identifier = identifier
        self._action = LOG_FSM_INITIALIZE(
            logger, fsm_identifier=identifier, fsm_state=unicode(fsm.state))


    def receive(self, input):
        """
        Add logging of state transitions to the wrapped state machine.

        @see: L{IFiniteStateMachine.receive}
        """
        action = LOG_FSM_TRANSITION(
            self.logger,
            fsm_identifier=self.identifier,
            fsm_state=unicode(self.state),
            fsm_rich_input=unicode(input),
            fsm_input=unicode(input.symbol()))
        with action as theAction:
            output = super(FiniteStateLogger, self).receive(input)
            theAction.addSuccessFields(
                fsm_next_state=unicode(self.state), fsm_output=[unicode(o) for o in output])

        if self._action is not None and self._isTerminal(self.state):
            self._action.addSuccessFields(
                fsm_terminal_state=unicode(self.state))
            # Better API will be available after
            # https://www.pivotaltracker.com/s/projects/787341/stories/59751070
            # is done.
            self._action.finishAfter(succeed(None))
            self._action = None

        return output


    def _isTerminal(self, state):
        """
        Determine if a state is terminal.

        A state is terminal if there are no outputs or state changes defined
        for any inputs in that state.

        @rtype: L{bool}
        """
        # This only works with _FiniteStateMachine not with arbitrary
        # IFiniteStateMachine since these attributes aren't part of the
        # interface.  This is private with the idea that maybe terminal should
        # be defined differently eventually - perhaps by accepting an explicit
        # set of terminal states in constructFiniteStateMachine.
        # https://www.pivotaltracker.com/story/show/59999580
        return all(
            transition.output == [] and transition.nextState == state
            for (input, transition)
            in self._fsm._fsm.table[state].iteritems())
