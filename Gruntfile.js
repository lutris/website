module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    less: {
      css: {
        options: {
            paths: 'components/bootstrap/less/'
        },
        files: {
          'public/css/lutris.css': ['common_static/css/lutris.less']
        }
      },
      min: {
        options: {
            yuicompress: true,
            paths: 'components/bootstrap/less/'
        },
        files: {
            'public/css/lutris.min.css': ['common_static/css/lutris.less']
        }
      }
    },
    coffee: {
      compile: {
        files: {
          'public/js/app.js': 'main/static/scripts/main.coffee'
        }
      }
    },
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      jquery: {
        files: {
          'public/js/jquery.min.js': ['components/jquery/jquery.js']
        }
      },
      bootstrap: {
        files: {
          'public/js/bootstrap.min.js': ['components/bootstrap/js/*.js']
        }
      },
      modernizr: {
        files: {
          'public/js/modernizr.min.js': ['components/modernizr/modernizr.js']
        }
      },
      app: {
        files: {
          'public/js/app.min.js': ['public/js/app.js']
        }
      }
    },
    watch: {
      options: {
        livereload: true
      },
      less: {
        files: 'common_static/css/lutris.less',
        tasks: ['less:css']
      },
      coffee: {
        files: ['main/static/scripts/main.coffee'],
        tasks: ['coffee']
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-coffee');

  grunt.registerTask('default', ['less', 'coffee', 'uglify']);
};

