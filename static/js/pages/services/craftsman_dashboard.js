document.addEventListener('DOMContentLoaded', function () {
    // ========================================
    // Tab Navigation - Smart Scroll Indicators
    // ========================================
    const tabNav = document.querySelector('.tab-nav');
    const activeTab = document.querySelector('.tab-nav-link.active');

    if (tabNav && activeTab) {
        // Auto-scroll active tab into view (centered if possible)
        setTimeout(() => {
            activeTab.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }, 100);

        // Function to update scroll indicators
        function updateScrollIndicators() {
            const scrollLeft = tabNav.scrollLeft;
            const maxScroll = tabNav.scrollWidth - tabNav.clientWidth;

            // Show left indicator if not at start
            if (scrollLeft > 10) {
                tabNav.classList.add('can-scroll-left');
            } else {
                tabNav.classList.remove('can-scroll-left');
            }

            // Show right indicator if not at end
            if (scrollLeft < maxScroll - 10) {
                tabNav.classList.add('can-scroll-right');
            } else {
                tabNav.classList.remove('can-scroll-right');
            }
        }

        // Update on scroll
        tabNav.addEventListener('scroll', updateScrollIndicators);

        // Update on resize
        window.addEventListener('resize', updateScrollIndicators);

        // Initial update
        updateScrollIndicators();
    }

    // ========================================
    // Calendar - Mobile Optimized
    // ========================================
    // Note: This logic depends on 'active_tab' and 'calendar_events' being available.
    // Since we are extracting to a static file, we need a way to pass these values.
    // The best approach is to check if the calendar element exists and if window.dashboardConfig is defined.

    var calendarEl = document.getElementById('calendar');

    if (calendarEl && window.dashboardConfig && window.dashboardConfig.activeTab === 'calendar') {
        // Detect mobile device
        const isMobile = window.innerWidth <= 768;

        var calendar = new FullCalendar.Calendar(calendarEl, {
            // Use list view on mobile for better readability
            initialView: isMobile ? 'listWeek' : 'dayGridMonth',

            // Simplified toolbar for mobile
            headerToolbar: {
                left: 'prev,next',
                center: 'title',
                right: isMobile ? 'listWeek,dayGridMonth' : 'dayGridMonth,timeGridWeek,listWeek'
            },

            locale: 'ro',
            firstDay: 1,

            buttonText: {
                today: 'Azi',
                month: 'Lună',
                week: 'Săptămână',
                list: 'Listă'
            },

            events: window.dashboardConfig.calendarEvents,

            eventClick: function (info) {
                info.jsEvent.preventDefault();
                if (info.event.url) {
                    window.location.href = info.event.url;
                }
            },

            eventDisplay: 'block',
            displayEventTime: false,
            height: 'auto',

            // Disable navLinks to prevent underlines on numbers
            navLinks: false
        });

        calendar.render();

        // Handle orientation change on mobile
        window.addEventListener('resize', function () {
            const newIsMobile = window.innerWidth <= 768;
            // We can't easily access the 'isMobile' variable from the closure if we re-declare it.
            // But we can check if the view needs changing.
            const currentViewType = calendar.view.type;
            const shouldBeListView = newIsMobile;

            // If we are on mobile but not in list view (or vice versa), reload might be needed or view change.
            // The original code reloaded the page.
            // Let's stick to the original logic for safety, but maybe just change view API?
            // Original: location.reload();

            // Let's try to be smarter: change view dynamically
            if (newIsMobile && currentViewType !== 'listWeek') {
                calendar.changeView('listWeek');
                calendar.setOption('headerToolbar', {
                    left: 'prev,next',
                    center: 'title',
                    right: 'listWeek,dayGridMonth'
                });
            } else if (!newIsMobile && currentViewType === 'listWeek') {
                calendar.changeView('dayGridMonth');
                calendar.setOption('headerToolbar', {
                    left: 'prev,next',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                });
            }
        });
    }
});
