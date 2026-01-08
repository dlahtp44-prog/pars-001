(function () {
    console.log("Responsive UI Loaded");

    // iOS 감지 (iPadOS 포함)
    const isIOS = () => {
        return /iPhone|iPad|iPod/.test(navigator.userAgent) ||
            (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    };

    if (isIOS()) {
        console.log("iOS device detected – applying viewport fix.");

        // iOS 100vh 버그 해결
        const setVH = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty("--vh", `${vh}px`);
        };

        setVH();
        window.addEventListener("resize", setVH);
    }
})();
