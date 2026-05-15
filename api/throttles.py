from rest_framework.throttling import UserRateThrottle


class EmpleadoRateThrottle(UserRateThrottle):
    scope = 'empleado'


class LoginRateThrottle(UserRateThrottle):
    scope = 'login'
