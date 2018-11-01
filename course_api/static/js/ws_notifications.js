// let notifications = [];
// let ws = 'wss://';
// if (location.protocol !== 'https:')
//     ws = 'ws://';
// let notifications_ws = new ReconnectingWebSocket(ws + window.location.host + "/api/ws/notifications");
// let handle_seen = (notif_id) => {
//     notifications_ws.send(JSON.stringify({command: 'delete', id: notif_id}))
// };
// notifications_ws.onmessage = function (event) {
//     let data = JSON.parse(event.data);
//     if (data.message === 'notifications_sent') {
//         notifications = data.data.reverse();
//         let notifs_windows = document.getElementById("notifications_window");
//         notifs_windows.innerHTML = '';
//         let length_notifs_not_seen = data.data.filter(notif => notif.seen === false).length;
//         if (length_notifs_not_seen > 0)
//             document.getElementById("notifications_count").dataset.count = "" + length_notifs_not_seen;
//         else
//             document.getElementById("notifications_count").setAttributeNode(document.createAttribute('hidden'));
//         if (data.data.length === 0) {
//             let node = document.createElement("div");
//             node.innerHTML = '<div style="border-bottom: 1px solid grey;background:#ffe3b4;padding-left:5px" class="dropdown-item">No New Alerts</div>';
//             notifs_windows.appendChild(node);
//             document.getElementById("notifications_count").setAttributeNode(document.createAttribute('hidden'));
//         }
//         else {
//             for (let notification of notifications) {
//                 let node = document.createElement("div");
//                 if (notification.type === 'waitlist') {
//                     if (notification.data.message === 'open_course')
//                         node.innerHTML = '<div style="border-bottom: 1px solid grey;background:#c8ffa8;padding-left:5px" class="dropdown-item">' + 'Course ' + notification.data.course.course_id + ' (' + notification.data.course.crn + ') is now OPEN!' + '<i style="float: right; margin-top:2px; font-size:20px" class="fas fa-times" onclick="handle_seen(' + notification.id + ')"></i>' + '</div>';
//                     if (notification.data.message === 'closed_course')
//                         node.innerHTML = '<div style="border-bottom: 1px solid grey;background:#FF9792;padding-left:5px" class="dropdown-item">' + 'Course ' + notification.data.course.course_id + ' (' + notification.data.course.crn + ') is now CLOSED.' + '<i style="float: right; margin-top:2px; font-size:20px" class="fas fa-times" onclick="handle_seen(' + notification.id + ')"></i>' + '</div>';
//                 }
//                 if (notification.type === 'message') {
//                     node.innerHTML = '<div style="border-bottom: 1px solid grey;background:#c8ffa8;padding-left:5px" class="dropdown-item">' + notification.data.message + '<i style="float: right; margin-top:2px; font-size:20px" class="fas fa-times" onclick="handle_seen(' + notification.id + ')"></i>' + '</div>';
//                 }
//                 // Create a text node
//                 notifs_windows.appendChild(node);
//             }
//             if (length_notifs_not_seen > 0)
//                 document.getElementById("notifications_count").removeAttribute('hidden');
//         }
//     }
// };
// notifications_ws.onopen = function (ev) {
//     setInterval(function () {
//         notifications_ws.send(JSON.stringify({command: 'ping'}))
//     }, 5000);
//     notifications_ws.send(JSON.stringify({command: 'get_notifications'}));
// };
// $('#navbarDropdown1').on('click', function (e) {
//     if (notifications_ws.readyState === 1) {
//         let seen_notifs = [];
//         for (let notif of notifications) {
//             seen_notifs.push(notif.id);
//         }
//         notifications_ws.send(JSON.stringify({command: 'seen_notifs', notifs: seen_notifs}))
//     }
// });
// $('.dropdown-menu').on('click', function (e) {
//     if ($(this).hasClass('dropdown-menu-form')) {
//         e.stopPropagation();
//     }
// });