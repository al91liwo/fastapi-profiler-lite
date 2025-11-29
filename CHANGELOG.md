## [0.3.4](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.3.3...v0.3.4) (2025-11-29)


### Bug Fixes

* include app root_path in dashboard static file URLs ([6e2a806](https://github.com/al91liwo/fastapi-profiler-lite/commit/6e2a806a4a29000c8d4b52507581dfa3c15bc049))

## [0.3.3](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.3.2...v0.3.3) (2025-06-04)


### Bug Fixes

* Enable instrumentation for AsyncEngine for async-slqalchemy ([9e67327](https://github.com/al91liwo/fastapi-profiler-lite/commit/9e67327d2e46b8061184fd3fe687420230fceb8d))


### Chores

* bump version to 0.3.2 [skip ci] ([b144d74](https://github.com/al91liwo/fastapi-profiler-lite/commit/b144d7418a7071808e7b5c8e6c5635c00000e479))
* update fastapi-profiler-rust dependency to >=0.3.2 ([03f99ff](https://github.com/al91liwo/fastapi-profiler-lite/commit/03f99ff08eac716530be37ed2ed4623f7d2e1bf0))
* update test cases for instrumentation to properly test profile tracking ([cf50e43](https://github.com/al91liwo/fastapi-profiler-lite/commit/cf50e43c6586a451893383d663f21e400b6334af))

## [0.3.2](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.3.1...v0.3.2) (2025-04-06)


### Continuous Integration

* update release workflow to sync rust dependency version ([1eb62d0](https://github.com/al91liwo/fastapi-profiler-lite/commit/1eb62d0b6ce42409f7f2595906cd3313679cdff1))


### Chores

* update fastapi-profiler-rust dependency to >=0.3.1 ([9fa34e4](https://github.com/al91liwo/fastapi-profiler-lite/commit/9fa34e4cf45bc7a8cc498be1cec1d59b1017ac7b))

## [0.3.1](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.3.0...v0.3.1) (2025-04-06)


### Continuous Integration

* fix version management of fastapi-profiler-rust ([bb707ab](https://github.com/al91liwo/fastapi-profiler-lite/commit/bb707ab60b1c13f3c15e324e6392c7481659bc90))

## [0.3.0](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.5...v0.3.0) (2025-04-06)


### Features

* Extend middleware, profiler, and stats for Database statistics and profiling ([c54942c](https://github.com/al91liwo/fastapi-profiler-lite/commit/c54942cd308e14b2250c87e4814ec151526e3067))
* Implement Database Profiler ([4feb091](https://github.com/al91liwo/fastapi-profiler-lite/commit/4feb091bd55189c6f127e4d48074dd775e6a6845))


### Bug Fixes

* CI/CD pytest by installing all extras ([0c8e1b1](https://github.com/al91liwo/fastapi-profiler-lite/commit/0c8e1b160e8ff66c95832a8703d110722439e327))


### Documentation

* Add extensive examples for Database Profiler ([8fdc36b](https://github.com/al91liwo/fastapi-profiler-lite/commit/8fdc36b918c338355653b7172fe88cacf4882894))
* Update README with pyo3 link and examples/ usage ([5bae178](https://github.com/al91liwo/fastapi-profiler-lite/commit/5bae1784d4d19c928ae3c62c29bc56c108def62f))


### Code Refactoring

* Order of pymethods in rustcore ([49c8ca0](https://github.com/al91liwo/fastapi-profiler-lite/commit/49c8ca0d7a312c153df2b734118987d77993b794))


### Tests

* Implement extensive instrumentation testing for edge cases ([deb711c](https://github.com/al91liwo/fastapi-profiler-lite/commit/deb711c0b44d934bf9ce92e8d0817d3c71861d97))


### Continuous Integration

* Enable windows build pipeline force remove wheels ([68e8ebd](https://github.com/al91liwo/fastapi-profiler-lite/commit/68e8ebdd47f1243a0efc00462a89f9cac944cf6c))
* fix Pipeline by installing built wheel after installing standard packages ([4200413](https://github.com/al91liwo/fastapi-profiler-lite/commit/42004139b61ca1762c2644a6fda50f920d85618f))
* Force clean build and consolidate twine upload pipeline ([c1e20e5](https://github.com/al91liwo/fastapi-profiler-lite/commit/c1e20e55e14df978176c50f1c327a4be69bb75f1))


### Chores

* **release:** 0.3.0 [skip ci] ([a61c5bb](https://github.com/al91liwo/fastapi-profiler-lite/commit/a61c5bbe4ab042b0e271ca14279d6231239df840))
* add fastapi-profiler-rust dependencies ([7a02100](https://github.com/al91liwo/fastapi-profiler-lite/commit/7a02100e2d92398270e83d66cac8d65d679de622))
* bump cargo.lock rustcore ([56dc6ca](https://github.com/al91liwo/fastapi-profiler-lite/commit/56dc6ca1859e30fcb9b78c9dd7fc83ebd28fca2f))
* bump rustcore version 0.2.19 ([e7044df](https://github.com/al91liwo/fastapi-profiler-lite/commit/e7044df0401872284c412e1e73913ef438e81995))
* **rustcore:** bump rustcore version to 0.2.20 [skip ci] ([80ca2cd](https://github.com/al91liwo/fastapi-profiler-lite/commit/80ca2cd5bc9475aa80196ab5ad0ce99764b678f2))
* integrate sqlparse and sqlalchemy to core ([0bcbf0e](https://github.com/al91liwo/fastapi-profiler-lite/commit/0bcbf0ef24740d3839b8dfbd577fd9aade19c49c))
* regenerate lockfile ([d97595d](https://github.com/al91liwo/fastapi-profiler-lite/commit/d97595dce7f8ceb5afe3ce6a2fe953c33ae2b115))
* ruff format ([a40cbad](https://github.com/al91liwo/fastapi-profiler-lite/commit/a40cbadfbd797a4b8ff6ed5b0ee6fcf962ab14d7))
* trigger pipeline ([d52fd4d](https://github.com/al91liwo/fastapi-profiler-lite/commit/d52fd4dcb920b8f7dfa619593bc571aadcd60a09))

## [0.3.0](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.5...v0.3.0) (2025-04-06)


### Features

* Extend middleware, profiler, and stats for Database statistics and profiling ([c54942c](https://github.com/al91liwo/fastapi-profiler-lite/commit/c54942cd308e14b2250c87e4814ec151526e3067))
* Implement Database Profiler ([4feb091](https://github.com/al91liwo/fastapi-profiler-lite/commit/4feb091bd55189c6f127e4d48074dd775e6a6845))


### Bug Fixes

* CI/CD pytest by installing all extras ([0c8e1b1](https://github.com/al91liwo/fastapi-profiler-lite/commit/0c8e1b160e8ff66c95832a8703d110722439e327))


### Documentation

* Add extensive examples for Database Profiler ([8fdc36b](https://github.com/al91liwo/fastapi-profiler-lite/commit/8fdc36b918c338355653b7172fe88cacf4882894))
* Update README with pyo3 link and examples/ usage ([5bae178](https://github.com/al91liwo/fastapi-profiler-lite/commit/5bae1784d4d19c928ae3c62c29bc56c108def62f))


### Code Refactoring

* Order of pymethods in rustcore ([49c8ca0](https://github.com/al91liwo/fastapi-profiler-lite/commit/49c8ca0d7a312c153df2b734118987d77993b794))


### Tests

* Implement extensive instrumentation testing for edge cases ([deb711c](https://github.com/al91liwo/fastapi-profiler-lite/commit/deb711c0b44d934bf9ce92e8d0817d3c71861d97))


### Continuous Integration

* Enable windows build pipeline force remove wheels ([68e8ebd](https://github.com/al91liwo/fastapi-profiler-lite/commit/68e8ebdd47f1243a0efc00462a89f9cac944cf6c))
* fix Pipeline by installing built wheel after installing standard packages ([4200413](https://github.com/al91liwo/fastapi-profiler-lite/commit/42004139b61ca1762c2644a6fda50f920d85618f))
* Force clean build and consolidate twine upload pipeline ([c1e20e5](https://github.com/al91liwo/fastapi-profiler-lite/commit/c1e20e55e14df978176c50f1c327a4be69bb75f1))


### Chores

* add fastapi-profiler-rust dependencies ([7a02100](https://github.com/al91liwo/fastapi-profiler-lite/commit/7a02100e2d92398270e83d66cac8d65d679de622))
* bump cargo.lock rustcore ([56dc6ca](https://github.com/al91liwo/fastapi-profiler-lite/commit/56dc6ca1859e30fcb9b78c9dd7fc83ebd28fca2f))
* bump rustcore version 0.2.19 ([e7044df](https://github.com/al91liwo/fastapi-profiler-lite/commit/e7044df0401872284c412e1e73913ef438e81995))
* **rustcore:** bump rustcore version to 0.2.20 [skip ci] ([80ca2cd](https://github.com/al91liwo/fastapi-profiler-lite/commit/80ca2cd5bc9475aa80196ab5ad0ce99764b678f2))
* integrate sqlparse and sqlalchemy to core ([0bcbf0e](https://github.com/al91liwo/fastapi-profiler-lite/commit/0bcbf0ef24740d3839b8dfbd577fd9aade19c49c))
* regenerate lockfile ([d97595d](https://github.com/al91liwo/fastapi-profiler-lite/commit/d97595dce7f8ceb5afe3ce6a2fe953c33ae2b115))
* ruff format ([a40cbad](https://github.com/al91liwo/fastapi-profiler-lite/commit/a40cbadfbd797a4b8ff6ed5b0ee6fcf962ab14d7))
* trigger pipeline ([d52fd4d](https://github.com/al91liwo/fastapi-profiler-lite/commit/d52fd4dcb920b8f7dfa619593bc571aadcd60a09))

## [0.2.5](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.4...v0.2.5) (2025-04-05)


### Documentation

* Add Rust core stats and Tabler.io UI details to README ([c9a28e4](https://github.com/al91liwo/fastapi-profiler-lite/commit/c9a28e4a124e45edf0567d94efa11becbab510f9))
* dashboard-demo.gif updated ([80911c8](https://github.com/al91liwo/fastapi-profiler-lite/commit/80911c86888f4adcaf13a991b774513ffc10e71d))
* update dashboard-demo.gif ([c240f9b](https://github.com/al91liwo/fastapi-profiler-lite/commit/c240f9b0dc60875cf30fd86c1bd6e3eb802ea84b))


### Code Refactoring

* ci/cd pipeline to integrate pypi publish procedure ([08cbc15](https://github.com/al91liwo/fastapi-profiler-lite/commit/08cbc1504458ec1012aa0d3403d76c3fd65ef3b7))
* use tabler.io with ApexChart Dashboard. Update StatusCodeDistribution in rustcore. ([9f14853](https://github.com/al91liwo/fastapi-profiler-lite/commit/9f14853c44213248fcc1b8796ca2f15f11e0f837))


### Chores

* bump poetry.lock ([2324ef1](https://github.com/al91liwo/fastapi-profiler-lite/commit/2324ef140204ee38cae825c25f638297ad487af7))
* **rustcore:** bump rustcore version to 0.2.14 [skip ci] ([d2e7336](https://github.com/al91liwo/fastapi-profiler-lite/commit/d2e73369bab6babe1166b15ce678cd798434a128))
* **rustcore:** bump rustcore version to 0.2.15 [skip ci] ([7366101](https://github.com/al91liwo/fastapi-profiler-lite/commit/7366101e0e4c8155493e095872b61ade18d85a5c))
* **rustcore:** bump rustcore version to 0.2.16 [skip ci] ([c90505f](https://github.com/al91liwo/fastapi-profiler-lite/commit/c90505f8a4254d53452a1bf094ab01dd568ad67e))
* **rustcore:** bump rustcore version to 0.2.17 [skip ci] ([e3e626e](https://github.com/al91liwo/fastapi-profiler-lite/commit/e3e626ec1596ebee323f57f0992a492fcbdb58b7))
* update release workflow and version to resolve pipeline issues ([e68e539](https://github.com/al91liwo/fastapi-profiler-lite/commit/e68e539933765272a818adc29132e3764d97494c))
* update release workflow to improve PyPI publishing ([5acad6a](https://github.com/al91liwo/fastapi-profiler-lite/commit/5acad6a2e70a213a806e21b2341373e1118591c5))

## [0.2.5](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.4...v0.2.5) (2025-04-05)


### Documentation

* Add Rust core stats and Tabler.io UI details to README ([c9a28e4](https://github.com/al91liwo/fastapi-profiler-lite/commit/c9a28e4a124e45edf0567d94efa11becbab510f9))
* dashboard-demo.gif updated ([80911c8](https://github.com/al91liwo/fastapi-profiler-lite/commit/80911c86888f4adcaf13a991b774513ffc10e71d))
* update dashboard-demo.gif ([c240f9b](https://github.com/al91liwo/fastapi-profiler-lite/commit/c240f9b0dc60875cf30fd86c1bd6e3eb802ea84b))


### Code Refactoring

* ci/cd pipeline to integrate pypi publish procedure ([08cbc15](https://github.com/al91liwo/fastapi-profiler-lite/commit/08cbc1504458ec1012aa0d3403d76c3fd65ef3b7))
* use tabler.io with ApexChart Dashboard. Update StatusCodeDistribution in rustcore. ([9f14853](https://github.com/al91liwo/fastapi-profiler-lite/commit/9f14853c44213248fcc1b8796ca2f15f11e0f837))


### Chores

* bump poetry.lock ([2324ef1](https://github.com/al91liwo/fastapi-profiler-lite/commit/2324ef140204ee38cae825c25f638297ad487af7))
* **rustcore:** bump rustcore version to 0.2.14 [skip ci] ([d2e7336](https://github.com/al91liwo/fastapi-profiler-lite/commit/d2e73369bab6babe1166b15ce678cd798434a128))
* **rustcore:** bump rustcore version to 0.2.15 [skip ci] ([7366101](https://github.com/al91liwo/fastapi-profiler-lite/commit/7366101e0e4c8155493e095872b61ade18d85a5c))
* **rustcore:** bump rustcore version to 0.2.16 [skip ci] ([c90505f](https://github.com/al91liwo/fastapi-profiler-lite/commit/c90505f8a4254d53452a1bf094ab01dd568ad67e))
* update release workflow and version to resolve pipeline issues ([e68e539](https://github.com/al91liwo/fastapi-profiler-lite/commit/e68e539933765272a818adc29132e3764d97494c))

## [0.2.4](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.3...v0.2.4) (2025-04-04)


### Code Refactoring

* rewrite the core as a rust module ([e347b7e](https://github.com/al91liwo/fastapi-profiler-lite/commit/e347b7eb9b5fefb7fb01cd7461887bc23ca9fcb4))

## [0.2.3](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.2...v0.2.3) (2025-04-02)


### Continuous Integration

* use conventionalcommits preset ([499616c](https://github.com/al91liwo/fastapi-profiler-lite/commit/499616c56c19dc7d95091012cfc2738b3cd58ce9))

## [0.2.2](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.1...v0.2.2) (2025-04-02)

## [0.2.1](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.0...v0.2.1) (2025-04-01)

## [0.2.1](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.2.0...v0.2.1) (2025-04-01)

# [0.2.0](https://github.com/al91liwo/fastapi-profiler-lite/compare/v0.1.0...v0.2.0) (2025-03-31)


### Features

* introduce conventional commits  and SemVer release pipeline ([#1](https://github.com/al91liwo/fastapi-profiler-lite/issues/1)) ([eb52322](https://github.com/al91liwo/fastapi-profiler-lite/commit/eb523220b78472139f4f0fa625fe9d26464fa654))

# Changelog

All notable changes to FastAPI Profiler Lite will be documented in this file.

## [0.1.0] - 2025-03-29
- Initial release with dashboard, request profiling, and performance metrics
- One-line integration with any FastAPI application
