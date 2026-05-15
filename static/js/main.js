document.addEventListener('DOMContentLoaded', function () {
  var alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    window.setTimeout(function () {
      if (window.bootstrap) {
        var instance = bootstrap.Alert.getOrCreateInstance(alert);
        instance.close();
      }
    }, 5000);
  });
});
