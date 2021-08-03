elifePipeline {
    node('containers-jenkins-plugin') {
        def commit
        def version

        stage 'Checkout', {
            checkout scm
            commit = elifeGitRevision()
            if (env.TAG_NAME) {
                version = env.TAG_NAME - 'v'
            } else {
                version = 'develop'
            }
        }

        stage 'Build and run tests', {
            try {
                withCommitStatus({
                    sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-build-all"
                }, 'ci-build-all', commit)
                withCommitStatus({
                    sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-lint"
                }, 'ci-lint', commit)
                withCommitStatus({
                    sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-pytest"
                }, 'ci-pytest', commit)
                withCommitStatus({
                    sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-end-to-end"
                }, 'ci-end-to-end', commit)
            } finally {
                sh "make ci-clean"
            }
        }

        elifeMainlineOnly {
            stage 'Merge to master', {
                elifeGitMoveToBranch commit, 'master'
            }

            stage 'Push unstable sciencebeam-parser image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-parser', commit)
                def unstable_image = image.addSuffixAndTag('_unstable', commit)
                unstable_image.tag('latest').push()
                unstable_image.push()
            }
        }

        elifeTagOnly { repoTag ->
            stage 'Push stable sciencebeam-parser image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-parser', commit)
                image.tag('latest').push()
                image.tag(version).push()
            }
        }
    }
}
