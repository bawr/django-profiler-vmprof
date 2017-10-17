app = angular.module(
    'vmprof', ['ngRoute', 'ngCookies', 'ngSanitize'], function($routeProvider) {

        $routeProvider
            .when('/', {
                templateUrl: '/static/vmprof/list.html',
                controller: 'list'
            })
            .when('/:log', {
                templateUrl: '/static/vmprof/details.html',
                controller: 'details'
            })
            .otherwise({
                redirectTo: '/'
            });

    }
);

app.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);

app.controller('main', function ($scope, $cookies, $location, $http) {
});

app.controller('list', function ($scope, $http, $interval) {
    angular.element('svg').remove();
    return;

    $scope.fetchAll = "";

    $scope.getLogs = function(showLoading) {
        if(showLoading) {
            $scope.loading = true;
        }
        $http.get('/api/log/', {params: {all:$scope.fetchAll}})
            .then(function(response) {
                $scope.logs = response.data.results;
                $scope.next = response.data.next;
                $scope.loading = false;
            });
    };


    $scope.more = function(next) {
        $http.get(next, {params: {all:$scope.fetchAll}})
            .then(function(response) {
                $scope.logs.push.apply($scope.logs,
                                       response.data.results);
                $scope.next = response.data.next;
            });

    };
    $scope.getLogs(true);

    $scope.background = function(time) {
        var seconds = moment.utc().diff(moment.utc(time, 'YYYY-MM-DD HH:mm:ss'), 'seconds');

        if (seconds > 500) {
            return {};
        }
        var color = Math.floor(205 + (seconds / 10));

        return {background: "rgb(255,255,"+ color +")"};
    };

});

function display_log($scope, $routeParams, $timeout, $location)
{
    var stats = $scope.stats;
    $scope.visualization = $routeParams.view || 'flames';
    console.log("display");

    $timeout(function () {
        $('[data-toggle=tooltip]').tooltip();
        var height = 800; //$('.table').height();
        var $visualization = $("#visualization");
        if ($visualization.length < 1)
            return;
        $scope.visualizationChange = function(visualization) {
            $scope.visualization = visualization;
            var stats = $scope.stats;
            if (visualization == 'list') {
                Visualization.listOfFunctions(
                    $("#visualization"),
                    height, $scope, $location,
                    stats.VM, true
                );
            }
            if (visualization == 'function-details') {
                Visualization.functionDetails($("#visualization"),
                    height, $routeParams.func_addr, $scope, $location);
            }
            if (visualization == 'list-2') {
                Visualization.listOfFunctions(
                    $("#visualization"),
                    height, $scope, $location,
                    stats.VM, false
                );
            }
            if (visualization == 'flames') {
                var d = stats.getProfiles($routeParams.id);
                $scope.root = d.root;
                var cutoff = d.root.total / 100;
                var addresses = $routeParams.id;
                var path_so_far;
                $scope.total_time = stats.allStats[d.root.addr].total / stats.nodes.total;
                $scope.self_time = stats.allStats[d.root.addr].self / stats.nodes.total;
                $scope.node_total_time = d.root.total / stats.nodes.total;
                $scope.node_self_time = d.root.self / stats.nodes.total;
                $scope.paths = d.paths;

                if (addresses) {
                    path_so_far = addresses.split(",");
                } else {
                    path_so_far = [];
                }
                Visualization.flameChart(
                    $("#visualization"),
                    height,
                    d.root,
                    $scope, $location,
                    cutoff, path_so_far,
                    stats.VM
                );
            }
        };

        $scope.visualizationChange($scope.visualization);
    });
    $scope.loading = false;
}

app.controller('details', function ($scope, $http, $routeParams, $timeout,
                                    $location) {
  angular.element('svg').remove();

  if ($scope.stats) {
      display_log($scope, $routeParams, $timeout, $location);
      return;
  }
  $scope.loading = true;

  $http.get('../json/' + $routeParams.log, {cache: true}
      ).then(function (response) {
          $scope.log = response.data;
          $scope.log_uuid = $routeParams.log;
          var data = response.data;
          if ('data' in data) {
            // the new profile is nested once more
            data = data.data;
          }
          $scope.stats = new Stats(data);
          display_log($scope, $routeParams, $timeout, $location);
  });
});
