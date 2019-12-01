struct = [{
    'name': 'Milestones',
    'height': '3em',
    'classes': 'gantt-row-milestone',
    'color': '#45607D',
    'tasks': [
        {
            'name': 'Kickoff',
            'color': '#93C47D',
            'from': '2013-10-07T07:00:00.000Z',
            'to': '2013-10-07T08:00:00.000Z',
            'data': 'Can contain any custom data or object',
            'id': '5d562f42-2c5d-9563-c063-4bb84eab671c',
            'dependencies': [
                {
                    'to': '1140e23b-09b0-0569-b2ed-b0a9e236bee0'
                }
            ]
        },
        {
            'name': 'Concept approval',
            'color': '#93C47D',
            'from': '2013-10-18T16:00:00.000Z',
            'to': '2013-10-18T16:00:00.000Z',
            'est': '2013-10-16T05:00:00.000Z',
            'lct': '2013-10-18T22:00:00.000Z',
            'progress': 100,
            'id': '1140e23b-09b0-0569-b2ed-b0a9e236bee0'
        },
        {
            'name': 'Development finished',
            'color': '#93C47D',
            'from': '2013-11-15T17:00:00.000Z',
            'to': '2013-11-15T17:00:00.000Z',
            'progress': 100,
            'id': 'bab90663-06b6-45d2-3379-18a0723094c1'
        },
        {
            'name': 'Shop is running',
            'color': '#93C47D',
            'from': '2013-11-22T11:00:00.000Z',
            'to': '2013-11-22T11:00:00.000Z',
            'progress': 50,
            'id': '7b71e34e-1606-5eb7-be9c-6bbc3acd9719'
        },
        {
            'name': 'Go-live',
            'color': '#93C47D',
            'from': '2013-11-29T15:00:00.000Z',
            'to': '2013-11-29T15:00:00.000Z',
            'progress': 0,
            'id': '0dc7f131-51cc-2dac-011f-57c5b6b72c0e'
        }
    ],
    'data': 'Can contain any custom data or object',
    'id': '10c9fea6-5e5e-7703-7e28-b870c7091f77'
},
    {
        'name': 'Status meetings',
        'tasks': [
            {
                'name': 'Demo #1',
                'color': '#9FC5F8',
                'from': '2013-10-25T13:00:00.000Z',
                'to': '2013-10-25T16:30:00.000Z',
                'progress': 20,
                'id': '74bd1c0b-ff82-f12f-78e9-8ad2b83d780f'
            },
            {
                'name': 'Demo #2',
                'color': '#9FC5F8',
                'from': '2013-11-01T14:00:00.000Z',
                'to': '2013-11-01T17:00:00.000Z',
                'id': 'bcd32ca9-6ad3-7629-2cc3-48aa9364aae6'
            },
            {
                'name': 'Demo #3',
                'color': '#9FC5F8',
                'from': '2013-11-08T14:00:00.000Z',
                'to': '2013-11-08T17:00:00.000Z',
                'id': 'c23a14be-179b-2858-3ec5-aa9a5751cbc2'
            },
            {
                'name': 'Demo #4',
                'color': '#9FC5F8',
                'from': '2013-11-15T14:00:00.000Z',
                'to': '2013-11-15T17:00:00.000Z',
                'id': '37c46a03-72c0-deb9-8289-351579e7460c'
            },
            {
                'name': 'Demo #5',
                'color': '#9FC5F8',
                'from': '2013-11-24T08:00:00.000Z',
                'to': '2013-11-24T09:00:00.000Z',
                'id': '19e09624-13c6-9f32-6d89-7c1d45865eec'
            }
        ],
        'id': 'f13b5de5-cc71-3113-fd5b-62eabb2ffdbe'
    },
    {
        'name': 'Kickoff',
        'movable': {
            'allowResizing': False
        },
        'tasks': [
            {
                'name': 'Day 1',
                'color': '#9FC5F8',
                'from': '2013-10-07T07:00:00.000Z',
                'to': '2013-10-07T15:00:00.000Z',
                'progress': {
                    'percent': 100,
                    'color': '#3C8CF8'
                },
                'movable': False,
                'id': 'a1d4dab9-dac2-4d68-765a-efee500b6783'
            },
            {
                'name': 'Day 2',
                'color': '#9FC5F8',
                'from': '2013-10-08T07:00:00.000Z',
                'to': '2013-10-08T15:00:00.000Z',
                'progress': {
                    'percent': 100,
                    'color': '#3C8CF8'
                },
                'id': 'cf46ca3b-362e-ebcc-854d-6e1b96786f34'
            },
            {
                'name': 'Day 3',
                'color': '#9FC5F8',
                'from': '2013-10-09T06:30:00.000Z',
                'to': '2013-10-09T10:00:00.000Z',
                'progress': {
                    'percent': 100,
                    'color': '#3C8CF8'
                },
                'id': '88449ae3-dbcb-3507-d6cc-24384529cb88',
                'dependencies': [
                    {
                        'to': '0ac2bb90-2d82-f804-c2c3-47513f58279b'
                    }
                ]
            }
        ],
        'id': 'f5dc05bf-504a-0eb9-b6e6-29af4c889090'
    },
    {
        'name': 'Create concept',
        'tasks': [
            {
                'name': 'Create concept',
                'content': '<i class=\'fa fa-cog\' ng-click=\'scope.handleTaskIconClick(task.model)\'></i> {{task.model.name}}',
                'color': '#F1C232',
                'from': '2013-10-10T06:00:00.000Z',
                'to': '2013-10-16T16:00:00.000Z',
                'est': '2013-10-08T06:00:00.000Z',
                'lct': '2013-10-18T18:00:00.000Z',
                'progress': 100,
                'id': '0ac2bb90-2d82-f804-c2c3-47513f58279b',
                'dependencies': [
                    {
                        'to': '659c53ab-c59d-da07-306d-640c9bc1d9be'
                    }
                ]
            }
        ],
        'id': '6b5f43d8-35a3-0954-df62-511d8d490077'
    },
    {
        'name': 'Finalize concept',
        'tasks': [
            {
                'name': 'Finalize concept',
                'color': '#F1C232',
                'from': '2013-10-17T06:00:00.000Z',
                'to': '2013-10-18T16:00:00.000Z',
                'progress': 100,
                'id': '659c53ab-c59d-da07-306d-640c9bc1d9be',
                'dependencies': [
                    {
                        'to': '60b5b586-1a53-0946-2149-c99ffe72f5bb'
                    }
                ]
            }
        ],
        'id': '79a8a86b-967a-3b0b-2be8-2cb1165bd74b'
    },
    {
        'name': 'Development',
        'children': [
            'Sprint 1',
            'Sprint 2',
            'Sprint 3',
            'Sprint 4'
        ],
        'content': '<i class=\'fa fa-file-code-o\' ng-click=\'scope.handleRowIconClick(row.model)\'></i> {{row.model.name}}',
        'id': '50fc00ab-dc14-6a5c-96aa-78402857597e'
    },
    {
        'name': 'Sprint 1',
        'tooltips': False,
        'tasks': [
            {
                'name': 'Product list view',
                'color': '#F1C232',
                'from': '2013-10-21T06:00:00.000Z',
                'to': '2013-10-25T13:00:00.000Z',
                'progress': 25,
                'id': '60b5b586-1a53-0946-2149-c99ffe72f5bb'
            }
        ],
        'id': '07db7056-ed92-7c4b-8087-35a1624580ad'
    },
    {
        'name': 'Sprint 2',
        'tasks': [
            {
                'name': 'Order basket',
                'dependencies': [
                    {
                        'from': 'Product list view',
                        'to': 'Checkout'
                    },
                    {
                        'to': '6ef011ef-7ced-41f5-6b23-2dbc44c464c7'
                    }
                ],
                'color': '#F1C232',
                'from': '2013-10-28T07:00:00.000Z',
                'to': '2013-11-01T14:00:00.000Z',
                'id': '4675dd34-8d34-9f08-1bea-a74329c65d6c'
            }
        ],
        'id': 'f7ec0ae6-c793-6c5c-754c-952c2d0f8454'
    },
    {
        'name': 'Sprint 3',
        'tasks': [
            {
                'name': 'Checkout',
                'color': '#F1C232',
                'from': '2013-11-04T07:00:00.000Z',
                'to': '2013-11-08T14:00:00.000Z',
                'id': '9bd6b4b8-9207-3aae-44e1-cdef9c81bdc5'
            }
        ],
        'id': '83d36f01-9c5e-c164-98a1-ccf6bd921d55'
    },
    {
        'name': 'Sprint 4',
        'tasks': [
            {
                'name': 'Login & Signup & Admin Views',
                'color': '#F1C232',
                'from': '2013-11-11T07:00:00.000Z',
                'to': '2013-11-15T14:00:00.000Z',
                'id': '450224dc-d7ee-8153-754e-e574c549f975'
            }
        ],
        'id': '9a1b8c1e-c711-6e53-5bb4-d76cd7aab4b2'
    },
    {
        'name': 'Hosting',
        'id': '66850d44-c81a-609b-68bb-3f34a060402b'
    },
    {
        'name': 'Setup',
        'tasks': [
            {
                'name': 'HW',
                'color': '#F1C232',
                'from': '2013-11-18T07:00:00.000Z',
                'to': '2013-11-18T11:00:00.000Z',
                'id': '6ef011ef-7ced-41f5-6b23-2dbc44c464c7'
            }
        ],
        'id': 'a77aa09a-1ef2-b9e4-36bd-666efe3ae3e7'
    },
    {
        'name': 'Config',
        'tasks': [
            {
                'name': 'SW / DNS/ Backups',
                'color': '#F1C232',
                'from': '2013-11-18T11:00:00.000Z',
                'to': '2013-11-21T17:00:00.000Z',
                'id': '196899fb-71c8-9ec7-dbf1-60b08aeac750'
            }
        ],
        'id': 'c4798cea-b117-491b-8204-9bc91fa0cde1'
    },
    {
        'name': 'Server',
        'parent': 'Hosting',
        'children': [
            'Setup',
            'Config'
        ],
        'id': 'd88810bf-bb7d-f7a1-f266-fca598a7a31a'
    },
    {
        'name': 'Deployment',
        'parent': 'Hosting',
        'tasks': [
            {
                'name': 'Depl. & Final testing',
                'color': '#F1C232',
                'from': '2013-11-21T07:00:00.000Z',
                'to': '2013-11-22T11:00:00.000Z',
                'classes': 'gantt-task-deployment',
                'id': 'e0341676-a645-4bb1-cae6-32fc196482c1'
            }
        ],
        'id': '5e61af4c-2bc0-6de3-e392-50f196b070dc'
    },
    {
        'name': 'Workshop',
        'tasks': [
            {
                'name': 'On-side education',
                'color': '#F1C232',
                'from': '2013-11-24T08:00:00.000Z',
                'to': '2013-11-25T14:00:00.000Z',
                'id': 'faefb435-b105-cf86-f35f-a20d515a5c33'
            }
        ],
        'id': '1ca61140-42e6-a04b-60ff-59c41b6fbe69'
    },
    {
        'name': 'Content',
        'tasks': [
            {
                'name': 'Supervise content creation',
                'color': '#F1C232',
                'from': '2013-11-26T08:00:00.000Z',
                'to': '2013-11-29T15:00:00.000Z',
                'id': 'ef3de1b1-ee93-751b-a4d3-1322a53262ec'
            }
        ],
        'id': '11bb7c74-05b7-52e9-7584-4981ebc576b8'
    },
    {
        'name': 'Documentation',
        'tasks': [
            {
                'name': 'Technical/User documentation',
                'color': '#F1C232',
                'from': '2013-11-26T07:00:00.000Z',
                'to': '2013-11-28T17:00:00.000Z',
                'id': '61f6169d-0ea9-4ccf-59bc-a6184e4d6410'
            }
        ],
        'id': '145fbba5-d17b-5724-4d37-b3a84fb7049c'
    }]


fields = []


def get_fields(data):
    global fields

    if isinstance(data, dict):
        for key, value in data.items():
            if 'name' in data.keys():
                if key not in fields:
                    fields.append(key)
            get_fields(value)
    elif isinstance(data, list):
        for item in data:
            get_fields(item)


get_fields(struct)
for item in sorted(fields):
    print("# "+ item)
